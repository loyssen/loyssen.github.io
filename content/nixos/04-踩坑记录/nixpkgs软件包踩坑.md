# nixpkgs 软件包踩坑记录

> 装软件时遇到的 nixpkgs 特有坑。套路总结：**装包前先验证可用性，报错先读完整信息**。

## 坑 1：pot 翻译——属性存在但装不上

**症状**：`nix eval` 检查 `builtins.hasAttr "pot" pkgs` 返回 `true`，
写进配置 rebuild 却报错：
```
error: 'pot' has been removed as it requires libsoup 2.4 which is EOL
```

**根因**：nixpkgs 把"已移除"的包保留为一个 **throw 别名**（占位并报出原因），
`hasAttr` 检查不出来。pot 依赖的 libsoup 2.4 已 EOL，stable 和 unstable 都被移除。

**修法**：换替代品。划词/OCR 翻译选 `crow-translate`；简单翻译选 `dialect`（GTK）。

**教训**：验证包可用性要用 `tryEval` 求值 version，不能只查属性存在：
```bash
nix eval --impure --expr '
  let pkgs = import <nixpkgs> { system="x86_64-linux"; config.allowUnfree=true; };
  in (builtins.tryEval (pkgs.<包名>.version)).success'
```

## 坑 2：QQ——上游下架旧安装包导致 404

**症状**：rebuild 时报：
```
curl: (22) The requested URL returned error: 404
error: cannot download QQ_3.2.27_260401_amd64_01.deb from any mirror
```

**根因**：nixpkgs 的 qq 是"下载腾讯官方 deb 再解包重打"的模式，
版本号 pin 死在 nixpkgs 里。腾讯 CDN **只保留最新版**，旧 deb 下架 → 404。
这不是网络问题（404 ≠ 被墙），换镜像源没用。

**修法**：用 unstable 里更新的版本（发布日期越近，deb 越可能还在）：
```nix
pkgs.unstable.qq
```

**教训**：凡"下载上游二进制重打"的包（qq/wechat/wpsoffice 等）都有这个时效性。
遇到 404 先查 unstable 有没有更新版本。

## 坑 3：legacyPackages 不带 unfree 许可

**症状**：overlay 这么写：
```nix
unstable = inputs.nixpkgs-unstable.legacyPackages.${system};
```
用 `pkgs.unstable.qq` 时报 `has an unfree license (‘unfree’), refusing to evaluate`。

**根因**：flake 的 `legacyPackages` 用默认 nixpkgs config 求值，`allowUnfree=false`。
它跟配置里的 `nixpkgs.config.allowUnfree = true` **互不相干**（那只管主 nixpkgs）。

**修法**：overlay 里手动 `import` 并显式开许可：
```nix
nixpkgs.overlays = [
  (final: prev: {
    unstable = import inputs.nixpkgs-unstable {
      system = prev.stdenv.hostPlatform.system;
      config.allowUnfree = true;
    };
  })
];
```

**教训**：凡是另一个 nixpkgs **实例**（overlay/import/legacyPackages），
许可配置都要单独给。

## 坑 4：yesplaymusic 在 stable 不存在

**症状**：装 yesplaymusic 报 attribute missing。

**根因**：包名/可用性随 nixpkgs 版本变化，25.11 里没有（unstable 也没有）。
当时误以为是"名字写错"，实际是包根本不在。

**修法**：换 `netease-cloud-music-gtk`（官方 GTK 客户端，nixpkgs 有打包，
二进制名是 `netease-cloud-music-gtk4`）。

**教训**：装包前三板斧：
```bash
# 1. 网页搜：https://search.nixos.org/packages
# 2. 命令行验证存在 + 可求值 + 版本
nix eval --impure --expr '...tryEval pkgs.<名>.version...'
# 3. 命令行模糊搜
nix search nixpkgs <关键词>
```

## 坑 5：kdeconnect 顶层属性不存在

**症状**：`pkgs.kdeconnect` 没有。

**根因**：KDE 系包陆续迁到 `kdePackages.*` 集合下，顶层别名有的删了。

**修法**：niri 等非 KDE 桌面更推荐 `valent`（KDE Connect 协议的 GTK 实现，
不拖 KDE 依赖）。

## 通用教训汇总

| 报错关键词 | 大概率原因 | 方向 |
|---|---|---|
| `has been removed` | 包被移除（依赖 EOL 等） | 找替代品 |
| `404 ... cannot download` | 上游二进制下架 | 换 unstable 新版 |
| `unfree license` | 另一个 nixpkgs 实例没开许可 | import 时给 config |
| `attribute ... missing` | 包名错/版本里没有 | search.nixos.org 核实 |
| 构建巨慢在下源码 | 没命中二进制缓存 | 查 substituters/网络 |
