# Omnipotent Youth Society Design

万能青年旅店视觉设计研究与 Agent Skill，重点为第二张专辑 **《冀西南林路行》 / Inside the Cable Temple**。

An independent visual design study and reusable agent skill inspired by **Omnipotent Youth Society**, with a focus on *Inside the Cable Temple*.

这是一份独立整理的设计参考，包含可复用技能、设计规范、带来源的图像档案和可离线运行的 HTML 样本；不是乐队或原设计师发布的官方规范。

## 内容

- [SKILL.md](skill/SKILL.md)：可整体复制使用的 `jixinan-visual-design` 技能。
- [DESIGN.md](DESIGN.md)：构图、色彩、字体、材料、交互与验收规则。
- [检索记录](research/SOURCES.md)：原始出处、证据层级与未确认事项。
- [素材索引](research/asset-manifest.json)：逐项来源、尺寸、文件名和下载状态。
- `page.template.html`：HTML / CSS / JavaScript 源模板，包含漫游、图录和规约三个视图。

## 使用技能

将整个 [`skill/`](skill/) 目录复制到你的 Agent 技能目录，并命名为 `jixinan-visual-design`。保留 `references/` 和 `assets/`，不要只复制入口文件。

使用 Codex 时，可放在 `~/.codex/skills/jixinan-visual-design/`，然后通过 `$jixinan-visual-design` 调用。技能文档本身不依赖 Python 或浏览器运行环境。

## 构建离线页面

需要 Python 3.11 或更新版本。在仓库根目录运行：

```sh
python -m pip install -r requirements.txt
python build.py
```

直接用浏览器打开生成的 `index.html`。图片和展示字体均已嵌入，浏览页面不需要联网；访问出处链接需要联网。

构建同时生成：

```text
dist/
  jixinan-visual-design.zip   # 完整技能包
  linlu-design-kit.zip        # 离线页面、设计文档、技能和素材索引
```

普通构建只写入当前仓库。需要显式安装到本机 Codex 时：

```sh
python build.py --install-skill
```

如已设置 `CODEX_HOME`，安装目标为其 `skills/` 子目录；否则使用 `~/.codex/skills/`。`--preview` 仅用于额外生成含本机绝对路径的 T3 HTML 预览文件，该文件不会提交到 Git。

## 验证

```sh
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python build.py
python tests/smoke.py
```

验证时阻止 HTTP/HTTPS 请求，检查 360、728、1440px 三档宽度，以及图片解码、主题切换、图录筛选、放大收起、章节切换、键盘操作和真实文件下载。截图与结果写入被 Git 忽略的 `artifacts/`。

GitHub Actions 在 push 和 pull request 时执行相同构建与检查，并上传生成的交付压缩包。

## 目录

```text
assets/          构建所需参考图像、长卷轻量版与字体
data/            图录标题、章节短文与来源数据
research/        检索记录与原始素材索引
scripts/         可移植的构建与打包逻辑
skill/           可独立复制的 Agent Skill
tests/           离线浏览器检查
DESIGN.md        设计规范
page.template.html
build.py         构建入口
```

仓库保留 38 张研究预览图及构建所需的轻量长卷。最初取得的两面高分辨率长卷约 298 MiB，保留在研究者本地；其来源仍在素材索引中，克隆仓库后无需下载这些原件即可构建。生成页面、重复缩略图、日志、网页抓取缓存和本机路径文件均不进入版本历史。

## 署名与使用范围

原专辑设计署名 **阮千瑞**。图像来自专辑实物资料、巡演材料和媒体访谈，各项出处见素材索引与检索记录；原作、摄影、其他专辑图片等权利属于相应权利人。本项目的网页转译和独立观察不代表乐队或设计师的官方解释。

Ma Shan Zheng 为本页采用的替代字库，并非原封面字体；字体遵循其 [SIL Open Font License](assets/FONT-LICENSE.txt)。仓库公开不改变第三方素材的授权状态，本仓库未对全部内容统一授予新的开源许可。
