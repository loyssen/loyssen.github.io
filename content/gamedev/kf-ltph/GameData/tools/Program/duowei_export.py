# -*- coding: utf-8 -*-

# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""通用多维表格直出器：.duowei → json + C#（不经中间表格与外部生成器）。

零项目知识：本文件只实现通用规则，不含任何具体类型名字面量。所有项目信息（类名映射/
明细表形态/输出目录/命名空间）来自上一级 tools/config.json 与源自带的类名映射表
（运行时读入）；json 导出集合即类名映射登记项（登记即导出，配置表清单已废除）。
导出器对现有游戏代码完全"盲"：生成结果与既有代码对不上
属"比对环节"的发现，不在生成环节修正。

通用规则全集（唯一逻辑）：
  表分类   类名映射表登记的表 → 独立数据类（导出集合=此类登记项，按表名稳定排序）；
           输出名集合含签名全部字段，大小写不敏感——`op>CompareOp` 解析后输出名 `op`
           即可命中）→ 明细表（类名优先取映射表，缺省取配置登记名；内嵌进
           引用方；可选 compare 规则把若干平铺列组装成嵌套共享 struct 成员——组装列同样
           按解析后输出名大小写不敏感匹配，命中成员名以表列解析后输出名为准；
           string_columns 强制 string 统一共享类型；明细类成员=属性）；
           配置 record_struct_tables 的表 →
           点号分组的独立类型文件：名列值 `A` → 类型 A、`A.B` → 类型 A 的属性成员 B
           （属性类型默认 string；singleSelect 且选项含基础类型词（整型/单精度小数/双精
           度小数/布尔/字符串）的列即类型源列——选项值基础词→映射类型、ASCII 标识符→
           原样作为 C# 类型名、其余→string 并告警；类型源列不成为成员；非身份列亦自动
           成为成员；emit=struct 默认 / class 控制产出 struct 还是类，base_class 仅
           class 可用、指定基类）；
           未登记的两字段纯文本表 → 字典表。
  键值解析 relation 指向 dict/record_struct 表时解引用为值列字符串：dict→第 2 列、
           record_struct→name_field 列（断链 FAIL 同引用规则）。
  字段文法 原始字段名 → {输出名, 前缀链, 合并组, struct 标记, 类型指定}：
           - 名字以 `_` 开头，或属插件内置列（ref_name 行编号）→ 跳过不导出
           - 先按 `@` 分组：`AA@BB` 与 `CC@BB` 同组，合并输出名=BB，AA/CC 为别名源列
           - 再按 `-` 拆：`AA-BB` → 前缀[AA]+字段BB；`@` 优先级高于 `-`
           - 名字以 `:` 开头 → 前缀组按 struct 生成（值类型）而非子类；struct 名 =
             前缀名 + 基类名（基类名以 I 开头则去 I，与 `-` 前缀子类拼接逻辑一致）
           - 名字含 `>`：`AA>T` → 指定输出成员的 C# 类型 T（如 Duration>float、
             Points>List<Vector2>，T 原样作为类型文本）；json 值按 T 转换（向量/向量
             列表 → {"x":..,"y":..} 形态，Newtonsoft 可直读）；singleSelect 列带 `>T`
             时以 T 为枚举类名生成枚举（源列选项=枚举成员，json 值输出选项名）；
             relation 列带 `>T` 时硬指定成员类型形态（List<T>/T[] → 数组，优先级高于
             cardinality/值形态推定），值解析与解引用行为不变
  类型判定 number：按字段属性精度定型——numberFormat.decimals 存在且 >0 时 1~6 位=
           float、>6 位=double（值全整数也按属性走，json 值输出浮点）；decimals=0/
           缺省 → 值扫描（全整数→int，含小数→float）；@合并组各源列 decimals 不一致
           FAIL。checkbox→bool；select→enum（选项=枚举名；带 `>T` 后缀→以 T 为
           枚举名生成）；text/autoNumber/longText→string，但全列值均为无损数字文本时
           按值推导为 int/float（存在前导零等形态损失则保持 string）。
  引用解引用 relation 目标缺失时视为自表引用；按目标分类输出：
           - 字典表 → 解析为其第二列值字符串
           - 输出名以 Id/Ids 结尾 → 取键（目标记录 Id 字段值；Id 是标识符非数值，取键
             类型一律 string，不按目标 Id 列值形态推导，与 ActorData 基类 Id:string
             一致；需要数字形态用 `>int`/`>List<int>` 硬指定覆盖，值解析不变）
           - 输出名=目标类名/表名 或其余结构目标 → 内嵌（递归导出为嵌套对象，环引用 FAIL）
           多值判定 cardinality=many → 数组、one → 标量；未登记时实际多元素 → 数组，
           内嵌引用仅单元素列表形态 → 按值形态推定数组并 WARN（值以列表存储即具备多选
           能力；键/值解析维持元素数判定）；目标记录不存在 → 断链 FAIL。
  子类生成 纯机械，与数据填充无关的"存在性"判断：子类只来自 `-` 前缀列，子类名 =
           前缀 + 具体基类名（基类名读自类名映射表）；没有某前缀列就不生成对应子类。
           判别 select（单选列选项全为多峰类名形态）不参与类名推导——其选项值仅作为
           判别数据忠实转记进 json 的 __type 首键（判别列不再重复输出为成员）。
           记录归属子类按填充判断：填了某前缀组任一列即归属该前缀子类，多组同填 FAIL；
           无填充归属基类。字段归属类为纯语法判断：无 `-` 前缀 → 基类字段（与哪些记录
           填充了值完全无关），有前缀 → 对应前缀子类字段。
  记录结构 剥壳（schemaVersion/id/name/fields/views/activeViewId/meta 等文档外壳、rec 的
           id/revision/syncUid 等记录外壳、插件内置列 ref_name）；每条记录输出 {输出名:值}；
           空值省略；有判别列的表首键 __type 转记判别值，无判别列但有子类的表 __type 为
           填充归属子类名（基类记录省略）。
  C# 生成  每个类型（类/接口/枚举/struct）独立一个 .cs 文件（文件名=类型名）；文件头
           不包裹 namespace（生成类型落全局命名空间，与游戏层一致），仅以 using 引用配
           置命名空间（默认 KFramwork；正文出现向量类型时自动追加 using UnityEngine）。
           按类别落 output.cs 配置的子目录：enum=枚举、event=记录类型表 struct、data=记录类型表
           class（AbstractData 派生）、actor_data=映射表产物（数据类/子类/接口具体类/
           `:` struct）、core=明细类/明细共享 struct/接口本体；
           同名类型（含枚举/struct/子类）跨表冲突 FAIL。
           原子落盘：全部 json 与 cs 先在内存生成，FAIL=0 才统一落盘——生成树全量重建
           （各 cs 目录及其父目录清残留，防旧版混入编译）；有 FAIL 时现有产物原样保留，
           不写半成品，杜绝新旧混杂。
           类名修饰符：`:` 前缀→struct（最高优先级）；`I` 前缀→interface（另生成去 I
           具体类承载数据）；`Data` 后缀→class : ActorData（不重复 Id/Name，成员值按基类
           string 形态输出，生成 CopyInstance(target) 把字段写入传入引用——零 new 零 GC、
           不复制 Id；子类 override 基类签名：先 base.CopyInstance(target) 再 is 模式转型
           拷贝自有字段）；默认→class。
           接口/struct 成员=属性（struct 一律属性），类成员=公有字段；接口表的具体类恰好
           实现接口全部成员（零额外属性）；`:` 前缀 struct 为独立类型，所属表为接口表时
           实现该接口并内部重新声明接口属性；struct 组不生成载体成员——json 中组内字段
           平铺进基类记录（无嵌套外壳、无 __type），C# 侧仅 struct 本体。
           成员名非合法标识符时净化（非法字符→`_`，全净化空→Field，冲突加序号）。

用法（任意目录）:
  python duowei_export.py [--config <配置路径>]     # 默认读上一级 tools/config.json
退出码 0=全部通过；1=存在 FAIL（断链/文法歧义/类型名冲突等）。
"""
import argparse
import glob
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ── 框架固定 schema（框架层约定，非项目数据）──────────────────────────────
ACTOR_BASE = "ActorData"                      # `Data` 后缀类的基类（Id/Name 为 string）
ACTOR_BASE_IDS = ("Id", "Name")               # 基类已有成员，子类不重复生成
PLUGIN_SKIP_FIELDS = frozenset({"ref_name"})  # 插件内置列（行编号），与 schemaVersion 等外壳同级剥除
CLASSLIKE_OPTION_RE = re.compile(r"^[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+$")  # 多峰类名形态
NUM_TEXT_RE = re.compile(r"^-?\d+(\.\d+)?$")
LEAD_ZERO_RE = re.compile(r"^-?0\d")
TYPE_TAG = "__type"                           # 子类记录的类型标记输出键
# 记录类型表（游戏事件/游戏数据）的类型列：singleSelect 且选项名全部可映射的列即类型源列
DICT_TYPE_TOKENS = {"整型": "int", "单精度小数": "float", "双精度小数": "double",
                    "布尔": "bool", "布尔值": "bool", "字符串": "string", "文本": "string"}
VECTOR_TYPES = {"Vector2": ("x", "y"), "Vector3": ("x", "y", "z"),
                "Vector4": ("x", "y", "z", "w"), "Quaternion": ("x", "y", "z", "w")}
CS_KEYWORDS = frozenset("""
abstract as base bool break byte case catch char checked class const continue decimal default
delegate do double else enum event explicit extern false finally fixed float for foreach goto if
implicit in int interface internal is lock long namespace new null object operator out override
params private protected public readonly ref return sbyte sealed short sizeof stackalloc static
string struct switch this throw true try typeof uint ulong unchecked unsafe ushort using var
virtual void volatile while
""".split())


def rel(base, p):
    return os.path.normpath(os.path.join(base, p))


def is_empty(v):
    return v is None or v == "" or v == []


def as_type(v, ctype):
    if v is None:
        return None
    if ctype == "int":
        return int(float(str(v)))
    if ctype == "float":
        return float(v)
    if ctype == "bool":
        return bool(v)
    return str(v)


class Diag:
    def __init__(self):
        self.fails = []
        self.warns = []

    def fail(self, msg):
        self.fails.append(msg)
        print("  [FAIL] " + msg)

    def warn(self, msg):
        self.warns.append(msg)
        print("  [WARN] " + msg)


class Table:
    """一张 .duowei 原始表：字段元数据 + 记录。"""

    def __init__(self, path):
        self.path = path
        self.stem = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        self.doc = doc
        self.name = str(doc.get("name") or self.stem)
        self.fields = doc.get("fields", [])
        self.records = doc.get("records", [])
        self.fid2field = {f["id"]: f for f in self.fields}
        self.field_names = [f["name"] for f in self.fields]
        self.rec_by_id = {r["id"]: r for r in self.records}

    @property
    def key(self):
        return self.name.lower()


class Store:
    """源目录全部 .duowei；按表名/文件名（大小写不敏感）寻址。"""

    def __init__(self, src_dir, map_path):
        self.tables = {}
        self.map_path = os.path.normpath(map_path)
        for fn in sorted(os.listdir(src_dir)):
            if not fn.endswith(".duowei"):
                continue
            t = Table(os.path.join(src_dir, fn))
            self.tables[t.key] = t
            self.tables.setdefault(t.stem.lower(), t)
        self.class_map = self._load_class_map()

    def _load_class_map(self):
        """类名映射表：前两条文本列，列1=表名、列2=类名（按列位取，不依赖列标题）。"""
        if not os.path.exists(self.map_path):
            raise SystemExit("[cfg] 类名映射表不存在: %s" % self.map_path)
        t = Table(self.map_path)
        cols = [f for f in t.fields if f.get("type") == "text"]
        if len(cols) < 2:
            raise SystemExit("[cfg] 类名映射表列形态异常（文本列不足两条）")
        c1, c2 = cols[0]["id"], cols[1]["id"]
        mapping = {}
        for rec in t.records:
            a = rec["values"].get(c1)
            b = rec["values"].get(c2)
            if a and b:
                mapping[str(a).strip().lower()] = str(b).strip()
        return mapping

    def find(self, name):
        if not name:
            return None
        s = str(name).strip().lower()
        if s.endswith(".duowei"):
            s = os.path.basename(s)[:-len(".duowei")]
        return self.tables.get(os.path.basename(s))

    def mapped_class(self, table):
        return self.class_map.get(table.key)


# ── 字段文法解析 ────────────────────────────────────────────────────────
class FieldSpec:
    """一个输出字段（可能是 @ 合并组）：来源列集合 + 文法产物。"""

    def __init__(self, out_name):
        self.out_name = out_name          # 输出名（@ 右侧或 `-` 末段）
        self.sources = []                 # [(fid, 原始名, 字段元数据)]
        self.prefix = ()                  # 组内统一前缀链
        self.struct_mark = False
        self.type_hint = None             # `>类型` 指定（None=按列类型推导）

    def add(self, fid, raw, meta, prefix, struct_mark):
        self.sources.append((fid, raw, meta))
        if self.sources and self.prefix != prefix:
            if len(self.sources) > 1 and self.prefix != prefix:
                raise ValueError("合并组前缀不一致")
        self.prefix = prefix
        self.struct_mark = self.struct_mark or struct_mark

    def first_fid(self):
        return self.sources[0][0]


def parse_name(raw):
    """原始字段名 → (跳过?, 前缀链, 输出名, 合并标记, struct 标记, 类型指定)。

    `AA>T` 后缀 = 指定输出成员使用类型 T（如 Duration>float、Points>List<Vector2>），
    T 原样作为 C# 类型文本；json 值按 T 转换（向量/向量列表解析为 {"x":..} 形态）。"""
    if raw.startswith("_"):
        return True, (), raw, False, False, None
    struct_mark = False
    name = raw
    if name.startswith(":"):
        struct_mark = True
        name = name[1:]
    type_hint = None
    if ">" in name:
        name, _, type_hint = name.partition(">")
        name, type_hint = name.strip(), type_hint.strip()
        if not name or not type_hint:
            raise ValueError("字段名 >类型 指定形态异常")
    merged = "@" in name
    prefix = ()
    if merged:
        left, _, out = name.rpartition("@")
        if "-" in left:
            prefix = tuple(left.split("-"))
    else:
        left, _, out = name.rpartition("-")
        prefix = (left,) if left else ()
    if "" in prefix:
        raise ValueError("字段名前缀链异常")
    return False, prefix, out, merged, struct_mark, type_hint


def parse_fields(table, diag):
    """字段文法解析 → 按输出名分组的 FieldSpec 有序列表（插件内置列剥壳跳过）。"""
    order = []
    groups = {}
    for f in table.fields:
        raw = f["name"]
        if raw in PLUGIN_SKIP_FIELDS:
            continue
        try:
            skip, prefix, out, merged, struct_mark, type_hint = parse_name(raw)
        except ValueError as e:
            diag.fail("%s.%s: %s" % (table.name, raw, e))
            continue
        if skip:
            continue
        if len(prefix) > 1:
            diag.fail("%s.%s: 多级前缀链暂不支持" % (table.name, raw))
            continue
        spec = groups.get(out)
        if spec is None:
            spec = groups[out] = FieldSpec(out)
            order.append(spec)
        if type_hint:
            if spec.type_hint and spec.type_hint != type_hint:
                diag.fail("%s.%s: >类型 指定冲突 %s / %s"
                          % (table.name, raw, spec.type_hint, type_hint))
            spec.type_hint = type_hint
        try:
            spec.add(f["id"], raw, f, prefix, struct_mark)
        except ValueError as e:
            diag.fail("%s.%s: %s" % (table.name, raw, e))
    return order


def parsed_out_names(table):
    """表全部字段的解析后输出名集合（小写）：文法按 parse_name（含 `>类型`/`@合并` 剥离）。

    文法异常项静默跳过（异常在建模期由 parse_fields 报告）；用于明细签名等无副作用比对。"""
    names = set()
    for f in table.fields:
        raw = f["name"]
        if raw in PLUGIN_SKIP_FIELDS:
            continue
        try:
            skip, _prefix, out, _merged, _struct, _hint = parse_name(raw)
        except ValueError:
            continue
        if not skip:
            names.add(out.strip().lower())
    return names


# ── 类型推导与成员模型 ──────────────────────────────────────────────────
class Member:
    def __init__(self, out, owner, spec):
        self.out = out                    # 净化后的输出名（json 键 = C# 成员名）
        self.owner = owner                # 归属类名
        self.spec = spec
        self.ctype = None                 # C# 类型文本
        self.kind = None                  # plain / enum / struct / rel_key / rel_dict / rel_embed
        self.is_list = False
        self.enum_name = None
        self.struct_model = None
        self.rel = None                   # RelationPlan


class StructModel:
    def __init__(self, name):
        self.name = name
        self.owner = None                 # 首登表名（跨表同名 FAIL 用）
        self.model = None                 # 所属 TableModel（接口实现信息）
        self.members = []                 # 自有成员（`:` 前缀列产出）


class EnumModel:
    def __init__(self, name, options):
        self.name = name
        self.owner = None                 # 首登表名（选项不一致 FAIL 用）
        self.options = options


class RelationPlan:
    def __init__(self):
        self.mode = None                  # key / dict / embed
        self.targets = {}                 # fid → Table（合并组各源列各自目标）
        self.key_ctype = "string"         # key 模式统一取键类型
        self.embed_models = {}            # fid → TableModel
        self.dict_value_fids = {}         # fid → 字典值列


class TableModel:
    """一张可导出表的完整模型（含子类/struct/enum 与记录导出）。"""

    def __init__(self, table, class_name, diag, store, builder, detail_spec=None):
        self.table = table
        self.diag = diag
        self.store = store
        self.builder = builder
        self.class_name = class_name
        self.detail_spec = detail_spec  # 明细表配置（含 compare 组装规则）
        self.iface = False
        self.specs = parse_fields(table, diag)
        self.discriminator_fid = None
        self.discriminator_opts = {}
        self.prefix_groups = {}
        self.subtypes = {}
        self.base_members = []
        self.struct_flat_members = []
        self.members_by_out = {}
        self.classify_name()  # 先定类名形态（设置 iface 标志，供构造期 concrete_name 使用）
        self._analyze()
        self._build_members()

    # ── 类名修饰符 ──
    def classify_name(self):
        n = self.class_name
        if n.startswith(":"):
            return "struct", n[1:]
        if len(n) > 1 and n[0] == "I" and n[1].isupper():
            self.iface = True
            return "interface", n
        if n.endswith("Data"):
            return "actordata", n
        return "class", n

    def concrete_name(self):
        """具体类名（去 I 接口前缀 / 去 : struct 前缀）——直接由类名计算，不依赖调用顺序。"""
        n = self.class_name
        if n.startswith(":"):
            return n[1:]
        if len(n) > 1 and n[0] == "I" and n[1].isupper():
            return n[1:]
        return n

    # ── 分析：判别列 / 前缀组 / 子类名（纯机械）──
    def _subtype_name(self, pfx):
        """子类名 = 前缀 + 具体基类名（基类名来自类名映射表，判别 select 选项不参与推导）。"""
        return pfx + self.concrete_name()

    def _analyze(self):
        t = self.table
        for f in t.fields:
            if f.get("type") != "singleSelect":
                continue
            names = [o["name"] for o in f.get("options", [])]
            if names and all(CLASSLIKE_OPTION_RE.match(n) for n in names):
                self.discriminator_fid = f["id"]
                self.discriminator_opts = {o["id"]: o["name"] for o in f["options"]}
                break
        for spec in self.specs:
            if spec.prefix and not spec.struct_mark:
                self.prefix_groups.setdefault(spec.prefix[0], []).append(spec)
        for pfx in self.prefix_groups:
            self.subtypes[self._subtype_name(pfx)] = []

    def _record_subtype(self, rec):
        """记录归属子类（按填充判断）；无前缀组表/无填充记录返回 None，多组同填返回 '!'。"""
        hit = None
        for pfx, specs in self.prefix_groups.items():
            for spec in specs:
                if any(not is_empty(rec["values"].get(fid)) for fid, *_ in spec.sources):
                    name = self._subtype_name(pfx)
                    if hit and hit != name:
                        return "!"
                    hit = name
                    break
        return hit

    # ── 成员构建 ──
    def _build_members(self):
        struct_parent_specs = []
        compare_cfg = (self.detail_spec or {}).get("compare") or {}
        compare_parts = {}   # 配置列名(小写) → FieldSpec（被 compare 嵌套组装消费的平铺列）
        if compare_cfg:
            by_lower = {s.out_name.strip().lower(): s for s in self.specs}
            for col in compare_cfg.get("columns", ()):
                spec = by_lower.get(str(col).strip().lower())
                if spec is None:
                    self.diag.fail("%s: compare 组装列 %s 不存在" % (self.table.name, col))
                else:
                    compare_parts[str(col).strip().lower()] = spec
        consumed = set(compare_parts.values())  # 命中成员名以解析后输出名为准
        for spec in self.specs:
            if spec in consumed:
                continue  # 平铺列被 compare 嵌套组装消费，不再独立成成员
            if spec.struct_mark and len(spec.prefix) == 1:
                # struct 名 = `:` 前缀名 + 具体基类名（基类名去 I 前缀，与 `-` 前缀子类拼接一致）
                sname = pascal_cs(spec.prefix[0] + self.concrete_name())
                sm = self.builder.struct_registry.get(sname)
                if sm is None:
                    sm = StructModel(sname)
                    sm.owner = self.table.name
                    sm.model = self
                    self.builder.struct_registry[sname] = sm
                elif sm.owner != self.table.name:
                    self.diag.fail("struct 名 %s 跨表冲突：%s / %s"
                                   % (sname, sm.owner, self.table.name))
                inner = self._make_member(spec, sname)
                if inner:
                    sm.members.append(inner)
                struct_parent_specs.append((spec, sname))
                continue
            if self.discriminator_fid and spec.first_fid() == self.discriminator_fid:
                continue  # 判别列不输出（判别数据由 __type 转记）
            # 字段归属 = 纯语法：有前缀归前缀子类，无前缀归基类（与数据填充无关）
            owner = self._subtype_name(spec.prefix[0]) if spec.prefix else None
            mem = self._make_member(spec, owner)
            if mem:
                self._register(mem)
        # `:` struct 不生成载体成员：json 中组内字段平铺进基类记录，C# 侧仅 struct 本体
        # （接口表 struct 重新声明接口属性；读取时按记录字段形态自然装载进对应 struct）
        self.struct_flat_members = [im for _, sname in struct_parent_specs
                                    for im in self.builder.struct_registry[sname].members]
        if compare_parts:
            self._build_compare_member(compare_cfg, compare_parts)

    def _build_compare_member(self, cfg, parts_map):
        """明细表 compare 组装：若干平铺列 → 嵌套共享 struct 成员（json/C# 同构嵌套）。"""
        local = StructModel(cfg["struct"])   # 发射用局部模型（成员绑本表字段）
        shim = FieldSpec(cfg["member"])
        string_cols = {str(c).strip().lower() for c in cfg.get("string_columns", ())}
        for col in cfg.get("columns", ()):
            spec = parts_map.get(str(col).strip().lower())
            if spec is None:
                continue
            pm = self._make_member(spec, None)
            if pm is None:
                continue
            if str(col).strip().lower() in string_cols:
                pm.kind, pm.is_list, pm.rel, pm.ctype = "plain", False, None, "string"
            local.members.append(pm)
            shim.sources += spec.sources
        if not local.members:
            self.diag.fail("%s: compare 组装无有效成员" % self.table.name)
            return
        self.builder.shared_struct(cfg["struct"], self, local.members)  # 类型声明走共享注册表
        mem = Member(self._safe_name(cfg["member"]), self.class_name, shim)
        mem.kind = "struct"
        mem.ctype = cfg["struct"]
        mem.struct_model = local
        self._register(mem)

    def _register(self, mem):
        if mem.owner in self.subtypes:
            self.subtypes[mem.owner].append(mem)
        else:
            self.base_members.append(mem)
        self.members_by_out[mem.out] = mem

    def _make_member(self, spec, owner):
        raw_types = {meta.get("type") for _, _, meta in spec.sources}
        out = self._safe_name(spec.out_name)
        mem = Member(out, owner or self.class_name, spec)
        if "relation" in raw_types:
            self._plan_relation(mem, spec)
            if spec.type_hint:
                # `>类型` 对关联列=硬指定成员类型形态：覆盖推定的 ctype/is_list（优先级最高），
                # 值解析/解引用路径不变
                mem.ctype = spec.type_hint
                mem.is_list = spec.type_hint.startswith("List<") or spec.type_hint.endswith("[]")
        elif "singleSelect" in raw_types:
            opts = []
            for _, _, meta in spec.sources:
                opts += [o["name"] for o in meta.get("options", [])]
            # `>类型` 后缀 = 枚举类名（以该名注册生成，选项=枚举成员）；
            # 缺省按输出名帕斯卡化（成员名保留源名）
            ename = spec.type_hint or pascal_cs(out)
            reg = self.builder.enum_registry.get(ename)
            if reg is None:
                reg = EnumModel(ename, opts)
                reg.owner = self.table.name
                self.builder.enum_registry[ename] = reg
            elif reg.options != opts:
                self.diag.fail("%s.%s: 枚举名 %s 与表 %s 选项不一致"
                               % (self.table.name, spec.out_name, ename, reg.owner))
            mem.kind = "enum"
            mem.enum_name = ename
            mem.ctype = ename
        elif spec.type_hint:
            mem.kind = "plain"
            mem.ctype = spec.type_hint
            mem.is_list = spec.type_hint.startswith("List<") or spec.type_hint.endswith("[]")
        elif "multiSelect" in raw_types:
            self.diag.warn("%s.%s: 多选列按字符串数组输出" % (self.table.name, spec.out_name))
            mem.kind = "plain"
            mem.is_list = True
            mem.ctype = "string"
        else:
            mem.kind = "plain"
            mem.ctype = infer_simple_ctype(self.table, spec, self.diag)
        return mem if mem.ctype else None

    def _safe_name(self, name):
        used = set(self.members_by_out) | {m.out for m in self.base_members}
        for members in self.subtypes.values():
            used.update(m.out for m in members)
        s = re.sub(r"[^A-Za-z0-9_]", "_", name)
        if not s or set(s) == {"_"}:
            s = "Field"
        if s[0].isdigit():
            s = "_" + s
        if s in CS_KEYWORDS:
            s = "@" + s
        base, n = s, 2
        while s in used:
            s = "%s_%d" % (base, n)
            n += 1
        return s

    def _plan_relation(self, mem, spec):
        diag, store = self.diag, self.store
        plan = RelationPlan()
        mem.rel = plan
        card = None
        max_len = 0
        list_form = False
        for fid, raw, meta in spec.sources:
            card = card or meta.get("relationCardinality")
            target = store.find(meta.get("relationTargetPath")) or self.table  # 目标缺失→自表
            plan.targets[fid] = target
            classification = self.builder.classify(target)
            if classification in ("dict", "record_struct"):
                plan.mode = plan.mode or "dict"
                plan.dict_value_fids[fid] = self.builder.value_field_id(target)
            elif mem.out.endswith("Ids") or mem.out.endswith("Id"):
                plan.mode = plan.mode or "key"
            else:
                plan.mode = plan.mode or "embed"
                tm = self.builder.model(target)
                if tm is None:
                    diag.fail("%s.%s: 内嵌目标 %s 模型构建失败" % (self.table.name, spec.out_name,
                                                                target.name))
                    return
                plan.embed_models[fid] = tm
            for rec in self.table.records:
                v = rec["values"].get(fid)
                if isinstance(v, list):
                    max_len = max(max_len, len(v))
                    if v:
                        list_form = True
        # 多选判定：登记 cardinality 优先（one=恒标量 / many=List）；缺失时实际多元素兜底
        # （数据自证无歧义，不告警）；仅内嵌结构引用按值形态推定——值以列表存储即具备多选
        # 能力（防插件不回写 relationCardinality），推定即告警提示配置缺失。键值/取键解析
        # 输出标量原语（string/数值），不参与值形态推定（维持元素数判定，防原语消费形态漂移）
        if card == "one":
            mem.is_list = False
        elif card == "many" or max_len > 1:
            mem.is_list = True
        elif list_form and plan.mode == "embed":
            mem.is_list = True
            diag.warn("%s.%s: 关联列未登记单/多选，按值形态推定 List"
                      % (self.table.name, spec.out_name))
        else:
            mem.is_list = False
        if plan.mode == "dict":
            mem.kind = "rel_dict"
            mem.ctype = "string"
        elif plan.mode == "key":
            mem.kind = "rel_key"
            for target in plan.targets.values():
                if next((f for f in target.fields if f["name"] == "Id"), None) is None:
                    diag.fail("%s.%s: 取键目标 %s 缺 Id 字段" % (self.table.name, spec.out_name,
                                                               target.name))
                    return
            # Id 是标识符非数值：取键一律 string（与 ActorData 基类 Id:string 一致），
            # 不按目标 Id 列值形态推导；需要数字形态由 `>int`/`>List<int>` 硬指定覆盖
            plan.key_ctype = "string"
            mem.ctype = plan.key_ctype
        else:
            mem.kind = "rel_embed"
            names = {tm.concrete_name() for tm in plan.embed_models.values()}
            if len(names) != 1:
                diag.fail("%s.%s: 内嵌目标类不唯一: %s" % (self.table.name, spec.out_name,
                                                          sorted(names)))
                return
            tname = names.pop()
            is_detail = all(self.builder.classify(t) == "detail" for t in plan.targets.values())
            if not is_detail and mem.out.lower() not in {
                    tname.lower(), *(t.key for t in plan.targets.values())}:
                diag.warn("%s.%s: 结构引用按内嵌组合输出（目标 %s）"
                          % (self.table.name, spec.out_name, tname))
            mem.ctype = tname
        if mem.is_list:
            mem.ctype = "List<%s>" % mem.ctype

    # ── 记录导出 ──
    def export_record(self, rec, path, out, diag):
        sub = self._record_subtype(rec)
        if sub == "!":
            diag.fail("%s[%s]: 多个前缀组同填，归属歧义" % (self.table.name, rec.get("id")))
        if self.discriminator_fid:
            # 判别列 → __type 忠实转记判别数据（不参与类名推导）
            name = self.discriminator_opts.get(rec["values"].get(self.discriminator_fid))
            if name is not None:
                out[TYPE_TAG] = name
        elif sub:
            # 无判别列但有子类：__type 为填充归属子类名（基类记录省略）
            out[TYPE_TAG] = sub
        members = list(self.base_members) + list(self.subtypes.get(sub or "", []))
        for mem in members:
            self._emit_member(rec, mem, path, out, diag)
        for im in self.struct_flat_members:
            self._emit_member(rec, im, path, out, diag)

    def _emit_member(self, rec, mem, path, out, diag):
        if mem.kind == "struct":
            # struct/嵌套组装成员：内部成员逐个发射，任一有值才输出外壳（无多源同填门禁）
            inner = {}
            for im in mem.struct_model.members:
                self._emit_member(rec, im, path, inner, diag)
            if inner:
                out[mem.out] = inner
            return
        spec = mem.spec
        filled = [fid for fid, *_ in spec.sources if not is_empty(rec["values"].get(fid))]
        if len(filled) > 1:
            diag.fail("%s[%s].%s: 合并列多源同填" % (self.table.name, rec.get("id"), spec.out_name))
            return
        if not filled:
            return
        fid = filled[0]
        meta = self.table.fid2field[fid]
        if mem.kind == "enum":
            out[mem.out] = opt_name(meta, rec["values"].get(fid))
            return
        if mem.kind == "plain":
            v = self._coerce_plain(rec["values"].get(fid), mem)
            if v is not None:
                out[mem.out] = v
            return

        plan = mem.rel
        target = plan.targets[fid]
        v = rec["values"].get(fid)
        ids = list(v) if isinstance(v, list) else ([] if v is None else [v])
        resolved = []
        for rid in ids:
            trec = target.rec_by_id.get(rid)
            if trec is None:
                diag.fail("%s[%s].%s: 断链 → %s[%s] 记录不存在"
                          % (self.table.name, rec.get("id"), spec.out_name, target.name, rid))
                continue
            if plan.mode == "dict":
                resolved.append(as_type(trec["values"].get(plan.dict_value_fids[fid]), "string"))
            elif plan.mode == "key":
                idf = next(f["id"] for f in target.fields if f["name"] == "Id")
                resolved.append(as_type(trec["values"].get(idf), plan.key_ctype))
            else:
                key = (target.key, trec["id"])
                if key in path:
                    diag.fail("%s[%s].%s: 内嵌环引用 → %s[%s]"
                              % (self.table.name, rec.get("id"), spec.out_name, target.name, rid))
                    continue
                nested = {}
                plan.embed_models[fid].export_record(trec, path | {key}, nested, diag)
                resolved.append(nested)
        if resolved:
            out[mem.out] = resolved if mem.is_list else resolved[0]

    def _coerce_plain(self, v, mem):
        if is_empty(v):
            return None
        ct = mem.ctype
        if ct == "int":
            return int(float(str(v)))
        if ct in ("float", "double"):
            return float(v)
        if ct == "bool":
            return bool(v) if isinstance(v, bool) else str(v).strip().lower() in ("true", "1")
        if ct.startswith("List<") or ct.endswith("[]"):
            inner = ct[ct.find("<") + 1:-1] if "<" in ct else ct[:-2]
            return [self._coerce_scalar(x, inner) for x in self._as_seq(v)]
        if ct in VECTOR_TYPES:
            return self._coerce_vector(v, ct)
        return str(v)

    def _as_seq(self, v):
        """文本值 → 列表：优先按 JSON 解析（几何列为 {"x","y"} 对象数组文本），退化为分隔符切分。"""
        if isinstance(v, list):
            return v
        try:
            arr = json.loads(v)
            if isinstance(arr, list):
                return arr
        except Exception:
            pass
        return [x.strip() for x in re.split("[;,，；]", str(v)) if x.strip()]

    def _coerce_scalar(self, x, ct):
        if ct in VECTOR_TYPES:
            return self._coerce_vector(x, ct)
        if ct == "int":
            return int(float(str(x)))
        if ct in ("float", "double"):
            return float(x)
        if ct == "bool":
            return bool(x) if isinstance(x, bool) else str(x).strip().lower() in ("true", "1")
        return str(x)

    def _coerce_vector(self, v, ct):
        """向量值 → {"x":..,"y":..}（成员名与 Unity 向量字段一致，Newtonsoft 可直读）。"""
        comps = VECTOR_TYPES[ct]
        if isinstance(v, dict):
            return {c: float(v[c]) for c in comps if c in v}
        try:
            arr = json.loads(v) if isinstance(v, str) else v
        except Exception:
            arr = None
        if isinstance(arr, dict):
            return {c: float(arr[c]) for c in comps if c in arr}
        if not isinstance(arr, (list, tuple)):
            arr = [t.strip() for t in str(v).strip("()[] ").split(",")]
        return {c: float(arr[i]) for i, c in enumerate(comps) if i < len(arr)}


# ── 简单列类型推导（值扫描）─────────────────────────────────────────────
def number_decimals_ctype(table, spec, diag):
    """number 列精度定类型：读各源列 numberFormat.decimals（缺失/0=不定型回退值扫描）。

    decimals>0 时按属性走（值全整数也定型）：1~6 → float、>6 → double；
    @合并组各源列 decimals 不一致 → FAIL（回退值扫描，产物因 FAIL 不落盘）。"""
    decimals = set()
    for _, _, meta in spec.sources:
        if meta.get("type") != "number":
            continue
        try:
            decimals.add(int((meta.get("numberFormat") or {}).get("decimals") or 0))
        except (TypeError, ValueError):
            diag.fail("%s.%s: numberFormat.decimals 非数值（%s）"
                      % (table.name, spec.out_name, meta.get("numberFormat")))
            return None
    if not decimals:
        return None
    if len(decimals) > 1:
        diag.fail("%s.%s: @合并组 decimals 不一致 %s"
                  % (table.name, spec.out_name, sorted(decimals)))
        return None
    d = decimals.pop()
    if d <= 0:
        return None
    return "double" if d > 6 else "float"


def infer_simple_ctype(table, spec, diag):
    raw = {meta.get("type") for _, _, meta in spec.sources}
    if "number" in raw:
        by_decimals = number_decimals_ctype(table, spec, diag)
        if by_decimals:
            return by_decimals
    vals = []
    for rec in table.records:
        for fid, *_ in spec.sources:
            v = rec["values"].get(fid)
            if not is_empty(v):
                vals.append(v)
    if not vals:
        return "string"
    types = {type(v).__name__ for v in vals}
    if "checkbox" in raw or types == {"bool"}:
        return "bool"
    if types <= {"int"}:
        return "int"
    if types <= {"int", "float"}:
        return "float"
    if types == {"str"} and raw & {"text", "autoNumber", "longText"}:
        if all(NUM_TEXT_RE.match(v) for v in vals):
            if any(LEAD_ZERO_RE.match(v) for v in vals):
                return "string"  # 前导零等形态损失，保持 string
            return "float" if any("." in v for v in vals) else "int"
    return "string"


def pascal_cs(name):
    """类型名（enum/struct）帕斯卡化——成员名保留源名，类型名遵守 C# 命名。"""
    s = safe_type_chars(name)
    return (s[0].upper() + s[1:]) if s else s


def safe_type_chars(name):
    s = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not s or set(s) == {"_"}:
        return "Type"
    if s[0].isdigit():
        s = "_" + s
    if s in CS_KEYWORDS:
        s = "@" + s
    return s


def opt_name(field_meta, opt_id):
    for o in field_meta.get("options", []):
        if o["id"] == opt_id:
            return o["name"]
    return opt_id


# ── 模型构建器（表分类 + 递归嵌入目标）──────────────────────────────────
class Builder:
    def __init__(self, store, diag, detail_specs, record_struct_specs):
        self.store = store
        self.diag = diag
        self.detail_specs = detail_specs or []  # [{class, fields, comment, compare}]，明细表签名（配置登记）
        self._models = {}
        self._building = set()
        self.enum_registry = {}    # 枚举名 → EnumModel（同命名空间去重）
        self.struct_registry = {}  # struct 名 → StructModel（`:` 产出/共享 compare struct）
        self.type_names = {}       # C# 类型名 → 来源描述（文件级冲突 FAIL）
        self.record_struct_specs = {}  # 表名(lower) → {table, name_field, skip_fields, emit}
        for s in record_struct_specs or []:
            self.record_struct_specs[str(s["table"]).strip().lower()] = s

    def detail_spec(self, table):
        """配置登记的明细签名命中（表解析后输出名集合含签名全部字段，大小写不敏感）。

        按解析后输出名而非原始列名比对——`op>CompareOp` 等带文法后缀的列解析后
        输出名恰为 `op`，本应命中。"""
        names = parsed_out_names(table)
        for spec in self.detail_specs:
            want = {str(f).strip().lower() for f in spec.get("fields", ())}
            if want <= names:
                return spec
        return None

    def classify(self, table):
        if os.path.normpath(table.path) == self.store.map_path:
            return "map"
        if self.store.mapped_class(table):
            return "mapped"
        if self.detail_spec(table):
            return "detail"
        if table.key in self.record_struct_specs:
            return "record_struct"
        if len(table.fields) == 2 and all(f.get("type") in ("text", "longText")
                                          for f in table.fields):
            return "dict"
        return "unknown"

    def value_field_id(self, target):
        """键值解析的目标值列：dict→第2列；record_struct→name_field 列。"""
        kind = self.classify(target)
        if kind == "dict":
            return target.fields[1]["id"]
        spec = self.record_struct_specs.get(target.key)
        if spec:
            f = next((f for f in target.fields if f["name"] == spec["name_field"]), None)
            if f is not None:
                return f["id"]
        self.diag.fail("表 %s 无法确定键值解析值列" % target.name)
        return None

    def shared_struct(self, name, model, parts):
        """共享 struct（如 compare 组装体）：首登建型，后用校验成员签名一致。"""
        sm = self.struct_registry.get(name)
        if sm is None:
            sm = StructModel(name)
            sm.owner = model.table.name
            sm.members = list(parts)
            self.struct_registry[name] = sm
            return sm
        sig = [(p.out, p.ctype) for p in parts]
        old = [(p.out, p.ctype) for p in sm.members]
        if sig != old:
            self.diag.fail("共享 struct %s 成员不一致：%s / %s（表 %s）"
                           % (name, old, sig, model.table.name))
        return sm

    def model(self, table):
        key = table.key
        if key in self._models:
            return self._models[key]
        kind = self.classify(table)
        if kind in ("dict", "map", "record_struct"):
            return None
        cls = self.store.mapped_class(table)
        dspec = self.detail_spec(table) if kind == "detail" else None
        if kind == "detail":
            cls = cls or dspec.get("class")
        if not cls:
            self.diag.fail("表 %s 无类名映射且非固定表" % table.name)
            return None
        if key in self._building:
            return None  # 模型级环：成员类型已可在先建模型中引用
        self._building.add(key)
        m = TableModel(table, cls, self.diag, self.store, self, detail_spec=dspec)
        self._models[key] = m
        self._building.discard(key)
        return m

    def declare(self, name, origin):
        """C# 类型名登记（每类型一个文件，同名冲突 FAIL）。"""
        if name in self.type_names:
            self.diag.fail("C# 类型名冲突：%s（%s / %s）"
                           % (name, self.type_names[name], origin))
            return False
        self.type_names[name] = origin
        return True


# ── C# 代码生成（每类型独立 .cs 文件）───────────────────────────────────
def cs_member_line(mem, as_property):
    decl = "%s %s" % (mem.ctype, mem.out)
    if as_property:
        return "        public %s { get; set; }" % decl
    return "        public %s;" % decl


def cs_file(usings, body_lines):
    """文件头不包裹 namespace（生成类落全局命名空间，与游戏层一致），以 using 引用配置
    命名空间；正文统一去一层缩进。usings=[配置命名空间, ...附加（如 UnityEngine）]。"""
    L = ["// 自动生成文件——由 duowei_export 从多维表格源生成，勿手改。",
         "using System;",
         "using System.Collections.Generic;"]
    L += ["using %s;" % u for u in usings if u]
    L.append("")
    L += [ln[4:] if ln.startswith("    ") else ln for ln in body_lines]
    return "\n".join(L) + "\n"


def body_enum(em):
    """枚举体：逐成员独立行（成员行 8 空格，末成员不带逗号，经 cs_file 统一去一层缩进）。"""
    L = ["    public enum %s" % em.name, "    {"]
    L += ["        %s," % o for o in em.options[:-1]]
    if em.options:
        L.append("        %s" % em.options[-1])
    L.append("    }")
    return L


def body_struct_lines(name, members):
    L = ["    public struct %s" % name, "    {"]
    L += [cs_member_line(m, True) for m in members]
    L.append("    }")
    return L


def body_struct(sm):
    """`:` 前缀 struct：成员一律属性；所属表为接口表时实现该接口（内部重新声明接口属性）。"""
    iface = None
    redecl = []
    if sm.model is not None:
        kind, _ = sm.model.classify_name()
        if kind == "interface":
            iface = sm.model.class_name
            # 接口属性在 struct 内重新声明；struct 载体成员不进接口契约（防 struct 自含环）
            redecl = [m for m in sm.model.base_members if m.kind != "struct"]
    L = ["    public struct %s%s" % (sm.name, " : %s" % iface if iface else ""), "    {"]
    L += [cs_member_line(m, True) for m in redecl]
    if redecl and sm.members:
        L.append("")
    L += [cs_member_line(m, True) for m in sm.members]
    L.append("    }")
    return L


def own_base_members(model, kind):
    """基类自有成员（ActorData 派生不重复 Id/Name；struct 载体成员仅驱动 json，不进 C#）。"""
    if kind == "actordata":
        return [m for m in model.base_members
                if m.out not in ACTOR_BASE_IDS and m.kind != "struct"]
    return [m for m in model.base_members if m.kind != "struct"]


def body_data_class(model):
    kind, cname = model.classify_name()
    own = own_base_members(model, kind)
    L = ["    public class %s%s" % (cname, " : %s" % ACTOR_BASE if kind == "actordata" else ""),
         "    {"]
    L += [cs_member_line(m, False) for m in own]
    if kind == "actordata":
        # CopyInstance：字段写入传入引用（零 new/零 GC），Id 不复制（Name 复制，维持既有规则）
        L.append("")
        L.append("        public virtual void CopyInstance(%s target)" % cname)
        L.append("        {")
        L.append("            target.Name = Name;")
        L += ["            target.%s = %s;" % (m.out, m.out) for m in own]
        L.append("        }")
    L.append("    }")
    return L


def body_subclass(model, sub):
    kind, _ = model.classify_name()
    members = model.subtypes[sub]
    L = ["    public class %s : %s" % (sub, model.concrete_name()), "    {"]
    L += [cs_member_line(m, False) for m in members]
    if kind == "actordata":
        if members:
            L.append("")
        # 虚方法：override 基类签名，先 base 拷基类字段，再 is 模式转型拷子类自有字段
        L.append("        public override void CopyInstance(%s target)" % model.concrete_name())
        L.append("        {")
        L.append("            base.CopyInstance(target);")
        if members:
            L.append("            if (target is %s t)" % sub)
            L.append("            {")
            L += ["                t.%s = %s;" % (m.out, m.out) for m in members]
            L.append("            }")
        L.append("        }")
    L.append("    }")
    return L


def collect_cs_files(builder):
    """全部模型 → {文件名（=类型名）: (类别, namespace 级代码行)}，每类型一个文件。

    类别（对应 output.cs 配置的子目录）：
      enum       select 推导的枚举
      event      记录类型表 emit=struct（事件 struct）
      data       记录类型表 emit=class（如 AbstractData 派生的模块数据类）
      actor_data 映射表产物（数据类/子类/接口具体类/`:` struct）
      core       明细类、明细共享 struct、接口本体
    """
    files = {}

    def add(name, origin, body, cat):
        if builder.declare(name, origin):
            files[name] = (cat, body)

    for em in builder.enum_registry.values():
        add(em.name, "enum（表 %s）" % em.owner, body_enum(em), "enum")
    for sm in builder.struct_registry.values():
        cat = "core" if sm.model is None else "actor_data"  # 共享组装 struct / `:` 表 struct
        add(sm.name, "struct（表 %s）" % sm.owner, body_struct(sm), cat)
    for m in builder._models.values():
        kind, cname = m.classify_name()
        if kind == "interface":
            # 接口成员 = 无前缀基础字段；struct 载体成员仅驱动 json 输出，不进任何 C# 类型。
            # 具体类恰好实现接口全部成员（零额外属性），与 struct 互不引用。
            iface_members = [mem for mem in m.base_members if mem.kind != "struct"]
            L = ["    public interface %s" % m.class_name, "    {"]
            L += [cs_member_line(mem, True) for mem in iface_members]
            L.append("    }")
            add(m.class_name, "interface（表 %s）" % m.table.name, L, "core")
            L = ["    public class %s : %s" % (m.concrete_name(), m.class_name), "    {"]
            L += [cs_member_line(mem, True) for mem in iface_members]
            L.append("    }")
            add(m.concrete_name(), "class（表 %s）" % m.table.name, L, "actor_data")
        elif kind == "struct":
            if m.subtypes:
                builder.diag.fail("struct 表 %s 不支持前缀子类" % m.table.name)
            add(cname, "struct（表 %s）" % m.table.name,
                body_struct_lines(cname, m.base_members), "actor_data")
        else:
            if getattr(m, "detail_spec", None):
                # 明细类：成员=属性（含 compare 嵌套成员），可选配置注释行
                L = []
                if m.detail_spec.get("comment"):
                    L.append("    // %s" % m.detail_spec["comment"])
                L += ["    public class %s" % cname, "    {"]
                L += [cs_member_line(mem, True) for mem in m.base_members]
                L.append("    }")
                add(cname, "class（明细表 %s）" % m.table.name, L, "core")
            else:
                add(cname, "class（表 %s）" % m.table.name, body_data_class(m), "actor_data")
        for sub in m.subtypes:
            add(sub, "subclass（表 %s）" % m.table.name, body_subclass(m, sub), "actor_data")
    # 固定表：记录类型表（名列点号分组：`A` 行→类型 A；`A.B` 行→类型 A 的成员 B；
    # emit=struct（默认）/class 控制产出 struct 还是类）
    for spec in builder.record_struct_specs.values():
        table = builder.store.find(spec["table"])
        if table is None:
            builder.diag.fail("record_struct 配置表不存在: %s" % spec["table"])
            continue
        nf = next((f for f in table.fields if f["name"] == spec["name_field"]), None)
        if nf is None:
            builder.diag.fail("record_struct 表 %s 缺名列 %s" % (table.name, spec["name_field"]))
            continue
        kw = "class" if spec.get("emit") == "class" else "struct"
        rcat = "data" if kw == "class" else "event"
        base_cls = spec.get("base_class")
        if base_cls and kw != "class":
            builder.diag.fail("record_struct 配置 %s：base_class 仅 emit=class 可用（struct 不能继承）"
                              % spec["table"])
            base_cls = None
        skip = {spec["name_field"], *spec.get("skip_fields", ())}
        # 类型源列：singleSelect 且选项名含可映射基础类型词（如 数值类型）——不成为成员。
        # 选项值三态：基础词→映射类型；ASCII 标识符→原样作为 C# 类型名（枚举/类引用）；
        # 其余（如"类"）→ string 并告警。
        def _opt_ct(n):
            ct = DICT_TYPE_TOKENS.get(n)
            if ct:
                return ct
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", n):
                return n
            builder.diag.warn("%s: 类型列选项 %s 无法映射，按 string" % (table.name, n))
            return "string"
        type_fid, type_id2ct = None, {}
        for f in table.fields:
            if f.get("type") != "singleSelect":
                continue
            names = [o["name"] for o in f.get("options", [])]
            if names and any(n in DICT_TYPE_TOKENS for n in names):
                type_fid = f["id"]
                type_id2ct = {o["id"]: _opt_ct(o["name"]) for o in f["options"]}
                break
        member_specs = [s for s in parse_fields(table, builder.diag)
                        if s.out_name not in skip
                        and type_fid not in {fid for fid, *_ in s.sources}]
        structs = {}   # 类型名 → 有序属性成员名列表
        propTypes = {}  # (类型名, 属性名) → C# 类型
        order = []
        for rec in table.records:
            raw = str(rec["values"].get(nf["id"]) or "").strip()
            if not raw:
                builder.diag.fail("%s[%s]: 名列 %s 为空，无法生成类型"
                                  % (table.name, rec.get("id"), spec["name_field"]))
                continue
            if "." in raw:
                grp, _, prop = raw.rpartition(".")
                if not grp or not prop:
                    builder.diag.fail("%s[%s]: 名 %s 点号形态异常" % (table.name, rec.get("id"), raw))
                    continue
                key = grp
                props = structs.setdefault(key, [])
                if prop not in props:
                    props.append(prop)
                if type_fid:
                    propTypes[(key, prop)] = type_id2ct.get(rec["values"].get(type_fid), "string")
            else:
                key = raw
                structs.setdefault(key, [])
            if key not in order:
                order.append(key)
        for sname_raw in order:
            props = structs.get(sname_raw, [])
            sname = safe_type_chars(sname_raw)
            suffix = " : %s" % base_cls if base_cls else ""
            L = ["    public %s %s%s" % (kw, sname, suffix), "    {"]
            for prop in props:  # 点号属性行：类型取类型源列（默认 string）
                ct = propTypes.get((sname_raw, prop), "string")
                L.append("        public %s %s { get; set; }" % (ct, safe_type_chars(prop)))
            for sp in member_specs:  # 非身份列（未来加的属性定义列）自动成为成员
                ct = sp.type_hint or infer_simple_ctype(table, sp, builder.diag)
                if ct:
                    L.append("        public %s %s { get; set; }" % (ct, sp.out_name))
            L.append("    }")
            if len(L) == 3:
                add(sname, "record %s（表 %s）" % (kw, table.name),
                    ["    public %s %s%s { }" % (kw, sname, suffix)], rcat)
            else:
                add(sname, "record %s（表 %s）" % (kw, table.name), L, rcat)
    return files


# ── 主流程 ─────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--config", default=os.path.join(here, os.pardir, "config.json"))  # tools/config.json（配置内相对路径以其所在目录为基准）
    args = ap.parse_args()
    cfg_path = os.path.abspath(args.config)
    with open(cfg_path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg_dir = os.path.dirname(cfg_path)
    src_dir = rel(cfg_dir, cfg["source_dir"])
    json_dir = rel(cfg_dir, cfg["output"]["json"])
    cs_dirs = {k: rel(cfg_dir, p) for k, p in cfg["output"]["cs"].items()}
    ns = cfg.get("namespace") or "KFramwork"

    diag = Diag()
    map_path = rel(cfg_dir, cfg["class_map_file"])
    if not os.path.exists(map_path):
        map_path = rel(src_dir, cfg["class_map_file"])  # 亦允许相对源目录寻址
    store = Store(src_dir, map_path)
    builder = Builder(store, diag, cfg.get("detail_tables"), cfg.get("record_struct_tables"))

    # 阶段一：全量内存生成（json 文本 + cs 文本）。有 FAIL 不动现有产物——杜绝半成品
    # 落盘与新旧混杂（"要点几次才全"的根因之一）。
    json_texts = {}   # 文件名 → 文本
    stats = []
    json_seen = {}
    # 导出集合 = 类名映射登记项（classify=mapped，遍历源目录自动发现）——映射表加/删
    # 一行即增减导出表，配置不再维护表名清单；按表名稳定排序保证产物与统计顺序确定。
    uniq_tables = {os.path.normpath(t.path): t for t in store.tables.values()}
    export_tables = [t for t in sorted(uniq_tables.values(), key=lambda t: t.name)
                     if builder.classify(t) == "mapped"]
    for table in export_tables:
        model = builder.model(table)
        if model is None:
            continue
        kind, cname = model.classify_name()
        out_records = []
        for rec in table.records:
            obj = {}
            model.export_record(rec, {(table.key, rec["id"])}, obj, diag)
            out_records.append(obj)
        if kind == "actordata":
            for obj in out_records:  # Id/Name 按基类 string 形态输出
                for k in ACTOR_BASE_IDS:
                    if k in obj and not isinstance(obj[k], str):
                        obj[k] = str(obj[k])
        jname = model.concrete_name()
        if jname in json_seen:
            diag.fail("json 输出名冲突：%s（%s / %s）" % (jname, json_seen[jname], table.name))
            continue
        json_seen[jname] = table.name
        json_texts[jname + ".json"] = json.dumps(out_records, ensure_ascii=False, indent=1) + "\n"
        stats.append((jname, len(out_records), len(model.base_members), len(model.subtypes)))

    # 全部模型（含内嵌明细目标）逐类型按类别生成 cs 文本
    files = collect_cs_files(builder)
    cs_texts = {}      # (类别目录, 文件名) → 文本
    for name in sorted(files):
        cat, body = files[name]
        d = cs_dirs.get(cat)
        if d is None:
            diag.fail("output.cs 缺类别目录 %s（类型 %s）" % (cat, name))
            continue
        usings = [ns]
        if any(t in "\n".join(body) for t in VECTOR_TYPES):
            usings.append("UnityEngine")
        cs_texts[(d, name + ".cs")] = cs_file(usings, body)

    by_cat = {}
    for name in sorted(files):
        by_cat.setdefault(files[name][0], []).append(name)
    if diag.fails:
        print("== 导出结果（FAIL=%d WARN=%d，产物未落盘，现有 Export/ 原样保留）=="
              % (len(diag.fails), len(diag.warns)))
        for cat in sorted(by_cat):
            print("  [%s] %d 个：%s" % (cat, len(by_cat[cat]), ", ".join(by_cat[cat])))
        return 1

    # 阶段二：原子落盘——生成树全量重建（json + 各 cs 类别目录及其父目录清残留，
    # 防旧版平级残留混入编译），随后一次性写入全部新产物。
    os.makedirs(json_dir, exist_ok=True)
    clean_dirs = []
    for d in cs_dirs.values():
        os.makedirs(d, exist_ok=True)
        clean_dirs.append(d)
        parent = os.path.dirname(os.path.normpath(d))
        if parent and parent not in clean_dirs:
            clean_dirs.append(parent)
    for f in glob.glob(os.path.join(json_dir, "*.json")):
        os.remove(f)
    for d in clean_dirs:
        for f in glob.glob(os.path.join(d, "*.cs")):
            os.remove(f)
    for fn in sorted(json_texts):
        with open(os.path.join(json_dir, fn), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json_texts[fn])
    for (d, fn) in sorted(cs_texts):
        with open(os.path.join(d, fn), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(cs_texts[(d, fn)])

    print("== 导出结果 ==")
    for cname, n, nm, nsub in stats:
        jpath = os.path.join(json_dir, cname + ".json")
        try:
            arr = json.load(open(jpath, encoding="utf-8"))
            ok = "OK" if len(arr) == n else "FAIL"
        except Exception as e:
            ok = "FAIL(%s)" % e
        print("  %-16s json=%s 条数=%d 成员=%d 子类=%d" % (cname, ok, n, nm, nsub))
    for cat in sorted(by_cat):
        print("  [%s] %d 个：%s" % (cat, len(by_cat[cat]), ", ".join(by_cat[cat])))
    print("  FAIL=%d WARN=%d" % (len(diag.fails), len(diag.warns)))
    return 1 if diag.fails else 0


if __name__ == "__main__":
    sys.exit(main())
