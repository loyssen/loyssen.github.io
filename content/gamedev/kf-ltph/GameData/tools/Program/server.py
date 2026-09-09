# -*- coding: utf-8 -*-

# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""导出工具后端：本地一体化服务（导出配置 + 一键导出 + .duowei 点位编辑桥）。

零第三方依赖（纯标准库 http.server/json/subprocess），uv 可直接跑。同一
127.0.0.1:8712 同时服务三类页面：
  - 导出工具.html（config.json 配置读写 + 一键直出导出）
  - 阵型点集编辑器.html / 路径点编辑器.html（.duowei 几何字段读写）

启动（推荐）: Obsidian 侧边栏 ▶「数据管线启动器」插件（静默后台）
启动（备用）: 双击 GameData/tools/Program/start.bat（独立最小化窗口 + 自检）
启动（命令行）: uv run GameData/tools/Program/server.py（任意 cwd，路径自定位）
                [-p 8712] [--dir <DuoWei 目录>] [--nobrowser]
停止:        Ctrl+C / 关闭承载窗口 / curl -X POST http://127.0.0.1:8712/shutdown

REST 面（响应统一 {"ok":true,...} / {"ok":false,"error":"..."}；CORS 全开 +
PNA 预检放行，file:// 页面也能 fetch）:

  导出工具：
  GET  /         → 返回 View/导出工具.html（工具页面本体）
  GET  /ping     → 健康检查（service=duowei-export-tools / pid / 配置路径 /
                   .duowei 表条数 / 导出占用态）
  GET  /config   → 读取 tools/config.json 全量返回
  POST /config   → 保存配置：body {"config":{...}}，仅接受白名单键
                   （source_dir / class_map_file / output / namespace），深度合并
                   到现有文件——tables / detail_tables / record_struct_tables 等
                   未编辑字段原样保留。写前 TEMP 时间戳备份，写后重读断言。
  POST /export   → subprocess 执行 `uv run duowei_export.py`（路径由本文件
                   位置自定位，跨机器通用；并发互斥 409；300s 超时），
                   返回 {ok, exit_code, stdout, stderr, duration_ms, timed_out}
  POST /apply    → 同 /export 的直出导出（响应字段 output=stdout+stderr 尾部
                   4000 字符，供编辑器状态条回显；与 /export 共用互斥与超时）
  POST /shutdown → 停止服务

  点位编辑（表文件每请求重读、无缓存——Obsidian 并发编辑即时可见）：
  GET  /list?table=formation|path            → 条目清单 [{id,name,(type)}]
                                                 （Name 排序；路径 type 按填充组判定）
  GET  /record?table=…&id=…                  → 单条几何字段值（文本已按 Fmt-R
                                                 规范化；路径 Type 合成为 Custom/Random）
  POST /record  body {"table":..,"id":..,"fields":{…}}
      → 最小手术写回单条：只改目标记录几何字段值 + revision+1 + updatedAt=当前
        ISO，其余字段/其余记录/文件格式逐字节原样。几何字段白名单（交叉校验）:
          formation:        Offsets
          path (Custom):    Points
          path (Random):    BoundInner + BoundOuter + WaypointCount（三键须齐，禁 Points）
        路径表为前缀分组形态（Custom-Points / Random-BoundInner 等，无 Type 列）：
        记录形态按填充组判定（Random 组任一有值即 Random，否则 Custom），
        逻辑字段名经 columns 映射解析物理列。列名匹配统一走 strip_type 文法
        （物理列剥 `>类型` 后缀再比对，如 Offsets>List<Vector2>），读写一律
        落真实列 fid——列名带任意类型后缀零影响。
        几何文本先 parse → 按 Fmt-R 重序列化再写（幂等）；写前整文件 JSON 校验，
        写后重读断言（不一致自动回滚写前原文并报错，不静默）。

Fmt-R（几何数字文本）= repr(float(v))（CPython float repr 最短往返；与
duowei_sync.py 的 fmt_r 同源）。

路径定位（全部由本文件位置自定位解析，无机器绑定，可整体迁移共享）：
本文件位于 <库根>/GameData/tools/Program/；config.json = 上一级 tools/；
duowei_export.py 与本文件同目录；三个工具页面在 tools/View/；
.duowei 表默认在 GameData/DuoWei/（--dir 覆盖）。
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

VERSION = "2.0.0"
SERVICE = "duowei-export-tools"
HERE = Path(__file__).resolve().parent            # <库根>/GameData/tools/Program
ROOT = HERE.parents[2]                            # 库根（= Obsidian vault 根）
CONFIG_PATH = HERE.parent / "config.json"         # tools/config.json
EXPORTER = HERE / "duowei_export.py"              # 同目录直出器
PAGE = HERE.parent / "View" / "导出工具.html"      # 页面目录
EXPORT_CMD = ["uv", "run", str(EXPORTER)]         # 自定位绝对路径，跨机器通用
EXPORT_TIMEOUT = 300                              # 秒（/export 与 /apply 同量级）
EDITABLE_KEYS = frozenset({"source_dir", "class_map_file", "output", "namespace"})
NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
BODY_LIMIT = 5 * 1024 * 1024                      # 请求体上限（几何点集可较大）

# .duowei 点位表（每请求重读，无缓存——Obsidian 并发编辑即时可见）
DUOWEI_DIR = HERE.parents[1] / "DuoWei"           # GameData/DuoWei（--dir 覆盖）
CONFIG_REL = os.path.relpath(CONFIG_PATH, ROOT).replace(os.sep, "/")  # 库根相对展示
TABLES = {
    "formation": {"file": "阵型.duowei",
                  "required": ["Name", "Id", "Shape", "Offsets"]},
    "path": {"file": "路径.duowei",
             "required": ["Name", "Id", "Description", "Custom-Points",
                          "Random-BoundInner", "Random-BoundOuter",
                          "Random-WaypointCount"],
             # 逻辑字段名 → 物理列名（前缀分组形态：Custom-*/Random-*；
             # 无 Type 列，记录形态看填充组——Random 组任一有值即 Random，否则 Custom）
             "columns": {"Points": "Custom-Points",
                         "BoundInner": "Random-BoundInner",
                         "BoundOuter": "Random-BoundOuter",
                         "WaypointCount": "Random-WaypointCount"}},
}


def strip_type(name):
    """物理列名 → 规格化名：剥 `>类型` 后缀（取首个 `>` 前部分，与导出器
    parse_name 同一文法）。列名匹配统一先规格化——物理列带任意类型后缀
    都不影响 required 校验与逻辑名→物理列解析。"""
    return str(name).partition(">")[0]


def _col(alias, logical):
    """逻辑字段名 → 规格化物理列名（无映射的表原样返回；统一走 strip_type，
    与 fmap 的「剥后缀名 → fid」键空间对齐）。"""
    return strip_type(TABLES[alias].get("columns", {}).get(logical, logical))

STARTED = time.strftime("%Y-%m-%dT%H:%M:%S")
EXPORT_LOCK = threading.Lock()
EXPORT_RUNNING = {"running": False, "startedAt": ""}
DW_LOCK = threading.Lock()                        # .duowei 写回互斥（多线程服务）


def log(msg):
    print("[export-tools %s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


# ── 配置文件读写（读容 BOM；文本级最小手术写回；写前 TEMP 备份 + 写后断言）──
def load_config():
    if not CONFIG_PATH.exists():
        raise RuntimeError("配置文件不存在: %s" % CONFIG_PATH)
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))


def _flatten(d, prefix=""):
    """嵌套 dict → {点号路径: 叶子值}（供文本补丁按键定位）。"""
    out = {}
    for k, v in d.items():
        key = "%s.%s" % (prefix, k) if prefix else str(k)
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            out[key] = v
    return out


def _patch_text(raw, leaves):
    """文本级叶子替换：只重写被修改键的字符串值，其余逐字节原样——保留既有
    排版（紧凑行内数组等，与 .duowei 最小手术写回同精神）。任一键在文本中
    非恰命中一次（缺失/多处/值非字符串）→ 返回 None（调用方回退全量序列化）。"""
    text = raw
    for key, val in leaves.items():
        if not isinstance(val, str):
            return None
        short = key.rsplit(".", 1)[-1]
        pat = re.compile(r'("%s"\s*:\s*)("(?:[^"\\]|\\.)*")' % re.escape(short))
        new_val = json.dumps(val, ensure_ascii=False)
        text, n = pat.subn(lambda m: m.group(1) + new_val, text, count=2)
        if n != 1:
            return None
    return text


def save_config(cfg, picked):
    """写回 config.json：优先文本级叶子替换（仅动被改键的值，含行尾
    风格原样保留）；补丁不适用时回退全量序列化（2 空格缩进 + 中文不转义 +
    尾换行）。写前 TEMP 时间戳备份；写后重读断言语义一致。"""
    raw = ""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8-sig", newline="") as fh:
            raw = fh.read()  # newline="" 不转换——CRLF/LF 原样进补丁
    text = _patch_text(raw, _flatten(picked)) if raw else None
    if text is None:
        text = json.dumps(cfg, ensure_ascii=False, indent=2) + "\n"
        log("config save: 文本补丁不适用（键缺失/非唯一），回退全量序列化")
    if json.loads(text) != cfg:  # 写前整文本校验：补丁结果必须与目标语义一致
        raise RuntimeError("写前校验不一致（文本补丁异常），未写盘")
    if CONFIG_PATH.exists():
        bak = Path(tempfile.gettempdir()) / ("data-pipeline-config.backup.%s.json"
                                             % time.strftime("%Y%m%d-%H%M%S"))
        try:
            shutil.copy2(CONFIG_PATH, bak)
            log("config backup: %s" % bak)
        except OSError as e:  # 备份失败不阻断保存（TEMP 异常属环境问题，原文件仍在 git）
            log("config backup FAILED (继续保存): %s" % e)
    CONFIG_PATH.write_text(text, encoding="utf-8", newline="\n")
    again = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    if again != cfg:
        raise RuntimeError("写后重读校验不一致（文件可能被并发修改），请重试")


def deep_merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            deep_merge(dst[k], v)
        else:
            dst[k] = v


def _decode_maybe(b):
    if b is None:
        return ""
    if isinstance(b, bytes):
        return b.decode("utf-8", errors="replace")
    return str(b)


# ── Fmt-R：几何数字文本 = repr(float(v))（CPython 最短往返，duowei_sync 同源）──
def fmt_r(v):
    if isinstance(v, str):
        t = v.strip()
        if t == "":
            raise ValueError("空值无法转数字: %s" % json.dumps(v, ensure_ascii=False))
        v = float(t)
    f = float(v)
    if not math.isfinite(f):
        raise ValueError("非有限数值: %s" % (v,))
    return repr(f)


# ── 几何文本 ↔ 点/边界（点集 "x,y" 键序定死幂等；容数字文本与 num_ok 同口径）──
def num_coerce(v, where, field):
    if v is None:
        return None
    f = None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        f = float(v)
    elif isinstance(v, str) and v.strip() != "":
        try:
            f = float(v.strip())
        except ValueError:
            f = None
    if f is None or not math.isfinite(f):
        raise ValueError("校验 FAIL: %s 字段 %s 值 %s 不是数值"
                         % (where, field, json.dumps(v, ensure_ascii=False)))
    return f


def parse_points(text, where, field):
    if text is None or str(text).strip() == "":
        return []
    try:
        j = json.loads(str(text))
    except (ValueError, TypeError) as e:
        raise ValueError("校验 FAIL: %s 字段 %s 不是合法点集 JSON: %s" % (where, field, e))
    items = j if isinstance(j, list) else [j]
    pts = []
    for i, p in enumerate(items):
        if not isinstance(p, dict):
            raise ValueError("校验 FAIL: %s 字段 %s 第 %s 点不是对象" % (where, field, i))
        pts.append((num_coerce(p.get("x"), where, "%s.x" % field),
                    num_coerce(p.get("y"), where, "%s.y" % field)))
    return pts


def parse_bound(text, where, field):
    if text is None or str(text).strip() == "":
        raise ValueError("校验 FAIL: %s 字段 %s 为空（Random 路径必填）" % (where, field))
    try:
        j = json.loads(str(text))
    except (ValueError, TypeError) as e:
        raise ValueError("校验 FAIL: %s 字段 %s 不是合法边界 JSON: %s" % (where, field, e))
    if not isinstance(j, dict):
        raise ValueError("校验 FAIL: %s 字段 %s 不是对象" % (where, field))
    return (num_coerce(j.get("x"), where, "%s.x" % field),
            num_coerce(j.get("y"), where, "%s.y" % field))


def fmt_points(pts):
    return "[" + ",".join('{"x":%s,"y":%s}' % (fmt_r(p[0]), fmt_r(p[1]))
                          for p in pts) + "]"


def fmt_bound(b):
    return '{"x":%s,"y":%s}' % (fmt_r(b[0]), fmt_r(b[1]))


def _round_half_up(v):
    """JS Math.round 对齐（.5 远离零方向取整；Python round 为银行家舍入）。"""
    return int(math.floor(v + 0.5)) if v >= 0 else int(math.ceil(v - 0.5))


def _to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _nz(v):
    return "" if v is None else v


def _iso_now():
    """JS new Date().toISOString() 对齐：UTC 毫秒 3 位 + Z。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _reject_const(name):
    raise ValueError("非法 JSON 常量: %s" % name)


def _atomic_write(path, text):
    """临时文件 + os.replace 原子落盘（读者不会读到半截文件；newline="\n"
    不做行尾转换，与文本内容逐字节一致）。"""
    tmp = path.with_name(path.name + ".tmp-write")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)


# ── .duowei 表加载（每请求重读，无缓存）──
def load_doc(alias):
    spec = TABLES.get(alias)
    if spec is None:
        raise ValueError("未知 table '%s'（可用: %s）" % (alias, "/".join(TABLES)))
    file = DUOWEI_DIR / spec["file"]
    if not file.exists():
        raise RuntimeError("缺少 .duowei 表文件: %s" % file)
    with open(file, "r", encoding="utf-8", newline="") as fh:
        raw = fh.read()
    had_bom = raw.startswith("\ufeff")
    try:
        doc = json.loads(raw[1:] if had_bom else raw)
    except ValueError as e:
        raise RuntimeError("%s JSON 解析失败（整文件校验）: %s" % (spec["file"], e))
    if (not isinstance(doc, dict) or not isinstance(doc.get("fields"), list)
            or not isinstance(doc.get("records"), list)):
        raise RuntimeError("%s 不是合法 .duowei 多维表格（缺 fields/records）" % spec["file"])
    # 列名文法规格化：物理字段名剥 >类型 后缀建映射，读写一律落真实列 fid
    # （列名再加/改类型后缀零影响；required/columns 逻辑契约不变）
    fmap = {}   # 规格化字段名（strip_type 后）→ 字段 id
    for f in doc["fields"]:
        key = strip_type(f.get("name"))
        if key in fmap:
            raise RuntimeError("%s 存在规格化后同名的字段: %s" % (spec["file"], key))
        fmap[key] = f.get("id")
    missing = [n for n in spec["required"] if n not in fmap]
    if missing:
        raise RuntimeError("%s 缺字段: %s" % (spec["file"], "/".join(missing)))
    return {"alias": alias, "file": file, "raw": raw, "had_bom": had_bom,
            "doc": doc, "fmap": fmap}


def find_record(loaded, rid):
    rec = next((r for r in loaded["doc"]["records"] if r.get("id") == rid), None)
    if rec is None:
        raise ValueError("记录不存在: %s id=%s" % (loaded["file"], rid))
    return rec


def _path_kind(loaded, values):
    """路径记录形态：Random 组（BoundInner/BoundOuter/WaypointCount）任一有值
    → Random，否则 Custom（前缀分组形态无 Type 列，归属看填充组）。"""
    fmap = loaded["fmap"]
    has_r = any(values.get(fmap.get("Random-%s" % k)) not in (None, "", "[]")
                for k in ("BoundInner", "BoundOuter", "WaypointCount"))
    return "Random" if has_r else "Custom"


# ── 云端行 → 编辑器输出（几何文本按 Fmt-R 规范化，与读/写回同一规则）──
def record_out(loaded, rec):
    fmap = loaded["fmap"]
    alias = loaded["alias"]
    v = rec.get("values") or {}
    name = v.get(fmap.get("Name")) or ""
    where = "[服务 %s %s]" % (loaded["file"].name, name)
    out = {"id": rec.get("id"), "Name": name}
    if alias == "formation":
        out["Id"] = _nz(v.get(fmap.get("Id")))
        out["Shape"] = _nz(v.get(fmap.get("Shape")))
        out["Offsets"] = fmt_points(parse_points(v.get(fmap.get("Offsets")), where, "Offsets"))
    else:
        kind = _path_kind(loaded, v)
        out["Id"] = _nz(v.get(fmap.get("Id")))
        out["Type"] = kind
        out["Description"] = v.get(fmap.get("Description"))
        if kind == "Random":
            out["BoundInner"] = fmt_bound(parse_bound(v.get(fmap.get(_col(alias, "BoundInner"))), where, "BoundInner"))
            out["BoundOuter"] = fmt_bound(parse_bound(v.get(fmap.get(_col(alias, "BoundOuter"))), where, "BoundOuter"))
            wc = num_coerce(v.get(fmap.get(_col(alias, "WaypointCount"))), where, "WaypointCount")
            out["WaypointCount"] = _round_half_up(wc)
        else:
            out["Points"] = fmt_points(parse_points(v.get(fmap.get(_col(alias, "Points"))), where, "Points"))
    return out


# ── POST /record：几何字段白名单 + 交叉校验 + Fmt-R 规范化 + 最小手术写回 + 重读断言 ──
def record_write(alias, rid, fields):
    if not isinstance(fields, dict) or not fields:
        raise ValueError("POST /record 缺 fields（或 fields 为空）")
    with DW_LOCK:
        loaded = load_doc(alias)
        fmap = loaded["fmap"]
        rec = find_record(loaded, rid)
        name = (rec.get("values") or {}).get(fmap.get("Name")) or ""
        where = "[服务 %s %s]" % (TABLES[alias]["file"], name)
        cells = {}  # 字段名 → 规范化后写入值（几何=Fmt-R 文本 / WaypointCount=int）
        if alias == "formation":
            for k in fields:
                if k != "Offsets":
                    raise ValueError("POST 拒绝: 阵型仅接受几何字段 Offsets（收到 '%s'）；"
                                     "Name/Id/Shape 等标识字段请在 Obsidian 侧维护" % k)
            cells["Offsets"] = fmt_points(parse_points(fields["Offsets"], where, "Offsets"))
        else:
            for k in fields:
                if k not in ("Points", "BoundInner", "BoundOuter", "WaypointCount"):
                    raise ValueError("POST 拒绝: 路径仅接受几何字段 "
                                     "Points/BoundInner/BoundOuter/WaypointCount（收到 '%s'）" % k)
            kind = _path_kind(loaded, rec.get("values") or {})
            if kind == "Custom":
                for k in fields:
                    if k != "Points":
                        raise ValueError("交叉校验 FAIL: %s Type=Custom 不接受字段 '%s'" % (where, k))
                if "Points" not in fields:
                    raise ValueError("POST 拒绝: %s Type=Custom 缺 Points" % where)
                cells["Points"] = fmt_points(parse_points(fields["Points"], where, "Points"))
            else:
                if "Points" in fields:
                    raise ValueError("交叉校验 FAIL: %s Type=Random 不接受 Points" % where)
                for need in ("BoundInner", "BoundOuter", "WaypointCount"):
                    if need not in fields:
                        raise ValueError("POST 拒绝: %s Type=Random 须齐 "
                                         "BoundInner/BoundOuter/WaypointCount（收到: %s）"
                                         % (where, ",".join(fields)))
                cells["BoundInner"] = fmt_bound(parse_bound(fields["BoundInner"], where, "BoundInner"))
                cells["BoundOuter"] = fmt_bound(parse_bound(fields["BoundOuter"], where, "BoundOuter"))
                wc = num_coerce(fields["WaypointCount"], where, "WaypointCount")
                if abs(wc - _round_half_up(wc)) > 1e-6:
                    raise ValueError("校验 FAIL: %s WaypointCount='%s' 要求整数"
                                     % (where, fields["WaypointCount"]))
                cells["WaypointCount"] = _round_half_up(wc)
        # 最小手术：只改目标记录的几何字段值 + revision+1 + updatedAt，其余逐字节原样
        new_rev = _to_int(rec.get("revision")) + 1
        new_at = _iso_now()
        values = rec.setdefault("values", {})
        for k, val in cells.items():
            values[fmap[_col(alias, k)]] = val
        rec["revision"] = new_rev
        rec["updatedAt"] = new_at
        try:
            text = json.dumps(loaded["doc"], ensure_ascii=False, indent=2) + "\n"
            json.loads(text, parse_constant=_reject_const)  # 写前整文件序列化校验
        except (ValueError, TypeError) as e:
            raise RuntimeError("写前校验 FAIL（未写盘）: %s" % e)
        if loaded["had_bom"]:
            text = "\ufeff" + text
        backup = loaded["raw"]  # 写前原文（断言失败时回滚）
        _atomic_write(loaded["file"], text)
        # 写后重读断言：目标字段/revision/updatedAt 落盘一致，不一致回滚原文并报错（不静默）
        try:
            with open(loaded["file"], "r", encoding="utf-8", newline="") as fh:
                s = fh.read()
            chk = json.loads(s[1:] if s.startswith("\ufeff") else s)
        except (OSError, ValueError) as e:
            _atomic_write(loaded["file"], backup)
            raise RuntimeError("写后重读解析失败（已回滚写前原文）: %s" % e)
        c2 = next((r for r in (chk.get("records") or []) if r.get("id") == rid), None)
        bad = []
        if c2 is None:
            bad.append("记录消失")
        else:
            cv = c2.get("values") or {}
            for k, val in cells.items():
                if cv.get(fmap[_col(alias, k)]) != val:
                    bad.append("字段 %s 落盘='%s' 期望='%s'"
                               % (k, cv.get(fmap[_col(alias, k)]), val))
            if c2.get("revision") != new_rev:
                bad.append("revision 落盘=%s 期望=%s" % (c2.get("revision"), new_rev))
            if c2.get("updatedAt") != new_at:
                bad.append("updatedAt 落盘=%s 期望=%s" % (c2.get("updatedAt"), new_at))
        if bad:
            _atomic_write(loaded["file"], backup)
            raise RuntimeError("写后重读断言失败（已回滚写前原文）: %s" % "; ".join(bad))
        log("write %s/%s: %s verified (revision=%s)"
            % (alias, name, ",".join(cells), new_rev))
        return {"written": list(cells),
                "record": record_out(load_doc(alias), c2 if c2 is not None else rec)}


# ── /export 与 /apply：触发 duowei_export.py（并发互斥 + 超时 + uv 缺失友好报错）──
def _run_exporter(h, responder):
    if not EXPORT_LOCK.acquire(blocking=False):
        return h.send_json({"ok": False,
                            "error": "导出进行中（%s 起），请稍候"
                                     % EXPORT_RUNNING["startedAt"]}, 409)
    EXPORT_RUNNING.update(running=True, startedAt=time.strftime("%Y-%m-%dT%H:%M:%S"))
    t0 = time.time()
    try:
        log("export start: %s (cwd=%s)" % (" ".join(EXPORT_CMD), ROOT))
        try:
            cp = subprocess.run(EXPORT_CMD, cwd=str(ROOT), capture_output=True,
                                timeout=EXPORT_TIMEOUT, encoding="utf-8",
                                errors="replace", creationflags=NO_WINDOW)
            payload = responder(cp.returncode, cp.stdout or "", cp.stderr or "",
                                int((time.time() - t0) * 1000), False)
        except subprocess.TimeoutExpired as e:
            payload = responder(None, _decode_maybe(e.stdout),
                                (_decode_maybe(e.stderr) or "")
                                + "\n[export-tools] 超时(%ds)终止" % EXPORT_TIMEOUT,
                                int((time.time() - t0) * 1000), True)
        except FileNotFoundError:
            payload = responder(None, "",
                                "找不到 uv——请安装 uv 并加入 PATH（https://docs.astral.sh/uv/）",
                                int((time.time() - t0) * 1000), False)
        log("export done: exit=%s %.1fs"
            % (payload.get("exit_code", payload.get("exitCode")),
               payload.get("duration_ms", 0) / 1000))
        return h.send_json(payload)
    finally:
        EXPORT_RUNNING["running"] = False
        EXPORT_LOCK.release()


def run_export(h):
    """POST /export：字段名供 导出工具.html 消费（stdout/stderr/exit_code…）。"""
    def mk(code, stdout, stderr, ms, timed_out):
        return {"ok": code == 0, "exit_code": code, "stdout": stdout,
                "stderr": stderr, "duration_ms": ms, "timed_out": timed_out,
                "command": " ".join(EXPORT_CMD)}
    return _run_exporter(h, mk)


def run_apply(h):
    """POST /apply：output=stdout+stderr 尾部 4000 字符（点位编辑器状态条回显）。"""
    def mk(code, stdout, stderr, ms, timed_out):
        return {"ok": code == 0, "exitCode": code,
                "output": (stdout + stderr)[-4000:]}
    return _run_exporter(h, mk)


# ── 路由 ────────────────────────────────────────────────────────────────
def _query_1(url, key):
    vals = parse_qs(url.query).get(key) or [""]
    return vals[0]


def _table_counts():
    counts = {}
    for alias in TABLES:
        try:
            counts[alias] = len(load_doc(alias)["doc"]["records"])
        except Exception as e:  # 表暂不可读不拖垮 /ping（自检仍报 ERR 明细）
            counts[alias] = "ERR: %s" % e
    return counts


def route_request(h, method, body):
    url = urlparse(h.path)
    route = "%s %s" % (method, url.path)
    if route == "GET /":
        return h.send_page()
    if route == "GET /ping":
        return h.send_json({"ok": True, "service": SERVICE, "version": VERSION,
                            "port": h.server.server_address[1], "pid": os.getpid(),
                            "startedAt": STARTED, "configPath": CONFIG_REL,
                            "vaultRoot": str(ROOT), "duoweiDir": str(DUOWEI_DIR),
                            "tables": _table_counts(),
                            "exportRunning": EXPORT_RUNNING["running"]})
    if route == "GET /config":
        cfg = load_config()
        return h.send_json({"ok": True, "config": cfg, "config_path": CONFIG_REL})
    if route == "POST /config":
        updates = (body or {}).get("config")
        if not isinstance(updates, dict) or not updates:
            raise ValueError("POST /config 缺 config 对象")
        picked = {k: v for k, v in updates.items() if k in EDITABLE_KEYS}
        if not picked:
            raise ValueError("无可保存的配置键（可编辑: %s）"
                             % ", ".join(sorted(EDITABLE_KEYS)))
        if "output" in picked and not isinstance(picked["output"], dict):
            raise ValueError("output 须为对象 {json, cs:{...}}")
        cs = (picked.get("output") or {}).get("cs")
        if cs is not None and not isinstance(cs, dict):
            raise ValueError("output.cs 须为对象 {core, enum, event, actor_data, data}")
        cfg = load_config()
        deep_merge(cfg, picked)
        save_config(cfg, picked)
        log("config saved: %s" % ", ".join(sorted(picked)))
        return h.send_json({"ok": True, "saved_keys": sorted(picked), "config": cfg,
                            "config_path": CONFIG_REL})
    if route == "GET /list":
        alias = _query_1(url, "table")
        loaded = load_doc(alias)
        fmap = loaded["fmap"]
        items = []
        for r in loaded["doc"]["records"]:
            v = r.get("values") or {}
            it = {"id": r.get("id"), "name": v.get(fmap.get("Name")) or ""}
            if alias == "path":
                it["type"] = _path_kind(loaded, v)
            items.append(it)
        items.sort(key=lambda it: str(it["name"]))  # 码点序（仅下拉显示顺序）
        return h.send_json({"ok": True, "table": alias, "count": len(items),
                            "items": items})
    if route == "GET /record":
        alias = _query_1(url, "table")
        rid = _query_1(url, "id")
        if not rid:
            raise ValueError("缺 id 参数")
        loaded = load_doc(alias)
        return h.send_json({"ok": True, "table": alias,
                            "record": record_out(loaded, find_record(loaded, rid))})
    if route == "POST /record":
        j = body or {}
        alias = str(j.get("table") or "")
        rid = str(j.get("id") or "")
        if not rid:
            raise ValueError("POST /record 缺 id")
        r = record_write(alias, rid, j.get("fields"))
        return h.send_json({"ok": True, "table": alias, "id": rid,
                            "written": r["written"], "record": r["record"]})
    if route == "POST /export":
        if not EXPORTER.exists():
            return h.send_json({"ok": False, "error": "导出器不存在: %s" % EXPORTER}, 500)
        return run_export(h)
    if route == "POST /apply":
        if not EXPORTER.exists():
            return h.send_json({"ok": False, "error": "导出器不存在: %s" % EXPORTER}, 500)
        return run_apply(h)
    if route == "POST /shutdown":
        h.send_json({"ok": True, "bye": True})
        log("shutdown requested.")
        threading.Timer(0.2, os._exit, args=(0,)).start()
        return
    return h.send_json({"ok": False, "error": "未知路由: %s" % route}, 404)


class Handler(BaseHTTPRequestHandler):
    server_version = SERVICE + "/" + VERSION
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        log("%s %s" % (self.address_string(), fmt % args))

    # 响应骨架：CORS 全开 + PNA 预检放行（file:// 页面 origin=null 也能 fetch）
    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()
        self.wfile.write(body)

    def send_page(self):
        try:
            body = PAGE.read_bytes()
        except OSError as e:
            return self.send_json({"ok": False, "error": "页面文件读取失败: %s (%s)"
                                                       % (PAGE, e)}, 500)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        if n > BODY_LIMIT:
            raise ValueError("请求体超限（>5MB）")
        return json.loads(self.rfile.read(n).decode("utf-8"))

    def safe_fail(self, e, code=400):
        log("REQ FAIL %s: %s" % (getattr(e, "__class__", type(e)).__name__, e))
        try:
            self.send_json({"ok": False, "error": str(e)}, code)
        except Exception:
            pass  # 响应已发出（连接断开等），不再抛

    def do_GET(self):
        try:
            route_request(self, "GET", None)
        except Exception as e:
            self.safe_fail(e)

    def do_POST(self):
        try:
            route_request(self, "POST", self.read_json_body())
        except Exception as e:
            self.safe_fail(e)

    def do_OPTIONS(self):
        self.send_json({"ok": True})


def ping_alive(port, timeout=2.0):
    """探测 port 上的实例是否为本服务且健康（返回 True/False）。"""
    try:
        with urlopen("http://127.0.0.1:%d/ping" % port, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("ok") is True and data.get("service") == SERVICE
    except Exception:
        return False


def kill_port_owner(port):
    """强杀占用 port 的进程（Windows netstat 解析；找不到返回 False）。"""
    if os.name != "nt":
        return False
    try:
        out = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"], capture_output=True, timeout=10,
            # 中文 Windows 的 netstat 输出为 GBK，UTF-8 严格解码会炸读取线程；仅匹配 ASCII 字段，替换坏字符无碍
            encoding="utf-8", errors="replace", creationflags=NO_WINDOW
        ).stdout or ""
    except Exception:
        return False
    killed = False
    for line in out.splitlines():
        parts = line.split()
        # LISTENING 行形如: TCP  127.0.0.1:8712  0.0.0.0:0  LISTENING  <pid>
        if len(parts) >= 5 and parts[3] == "LISTENING" and parts[1].endswith(":%d" % port):
            pid = parts[4]
            if pid.isdigit() and int(pid) != os.getpid():
                subprocess.run(["taskkill", "/F", "/PID", pid],
                               capture_output=True, timeout=10,
                               creationflags=NO_WINDOW)
                killed = True
    return killed


class ExclusiveServer(ThreadingHTTPServer):
    # Windows 上 SO_REUSEADDR（HTTPServer 默认开）允许双进程绑同一端口造成劫持，
    # 关闭后端口被占才会抛 OSError，走下方占用检测/自愈路径
    allow_reuse_address = False


def bind_server(port):
    """绑定端口；被占时先探测健康实例（复用退出），僵尸则强杀重试。"""
    for attempt in range(2):
        try:
            return ExclusiveServer(("127.0.0.1", port), Handler)
        except OSError:
            if ping_alive(port):
                print("[export-tools] 端口 %d 已有健康实例在运行，复用之（本进程退出）" % port)
                return None
            if attempt == 0 and kill_port_owner(port):
                print("[export-tools] 端口 %d 被僵尸进程占用，已强杀，重试绑定" % port)
                time.sleep(0.5)
                continue
            raise
    return None


def main():
    global DUOWEI_DIR
    ap = argparse.ArgumentParser(description="duowei 导出工具本地后端"
                                             "（配置读写 + 一键导出 + .duowei 点位编辑桥）")
    ap.add_argument("-p", "--port", type=int, default=8712, help="监听端口（默认 8712）")
    ap.add_argument("--dir", default="", help=".duowei 表目录（默认 同级 DuoWei/）")
    ap.add_argument("--nobrowser", action="store_true", help="启动后不自动打开浏览器")
    args = ap.parse_args()
    if args.dir:
        DUOWEI_DIR = Path(args.dir).resolve()
    if not DUOWEI_DIR.exists():
        print("[export-tools] DuoWei 目录不存在: %s（--dir 指定正确路径）" % DUOWEI_DIR)
        return 2
    url = "http://127.0.0.1:%d/" % args.port
    try:
        httpd = bind_server(args.port)
    except OSError as e:
        print("[export-tools] 启动失败: %s（端口被占用？可能已有实例——浏览器开 %s 或 -p 换端口）"
              % (e, url))
        return 1
    if httpd is None:
        return 0  # 已有健康实例，复用即可
    log("%s v%s listening on %s （vault=%s；duowei=%s；停止: 关闭本窗口 / POST /shutdown）"
        % (SERVICE, VERSION, url, ROOT, DUOWEI_DIR))
    # 服务器启动后不在浏览器打开（在 Obsidian 内使用 Custom Frames / HTML Reader）
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
