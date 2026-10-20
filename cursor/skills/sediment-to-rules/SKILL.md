---
name: sediment-to-rules
description: 把项目里得出的通用、可复用的经验沉淀进 Cursor 全局规则，并按规范归位：通用的工作范式和坑写进 User Rules 里的「通用工作约束」，特定语言的经验写进按 paths 挂上的 skill（如 python-pitfalls、go-pitfalls），和 shell / 本机环境有关的写进 shell-pitfalls，特定的工作流程写成 ~/.cursor/skills 里的 skill。凡是用户说"把这个经验沉淀一下 / 记到全局 / 记到全局 CLAUDE.md / 记到 Cursor 规则 / 这个坑以后都要注意 / 更新一下通用规范 / 这条写进规则"，务必使用本技能；在一个项目里踩了坑、得出了换个项目也成立的结论之后，也应主动提议用它沉淀。只针对全局、跨项目的规则——项目专有的约定写进该仓库自己的 AGENTS.md / .cursor/rules，不用本技能。
---

# 把经验沉淀进 Cursor 全局规则

全局规则分两处：通用的部分在 Cursor Settings 的 **User Rules**（标题「通用工作约束」那一条），每个会话都会加载，写进去的东西影响所有项目；按场景才用得上的部分是 `~/.cursor/skills/` 下的 skill。所以要做对两件事：**只放真正跨项目通用的**，**放对位置**。否则 User Rules 会越长越乱，该生效的规则被淹没；只跟某门语言有关的内容，还会在每个会话里白白占上下文。

不再使用 `~/.cursor/rules/*.mdc`：那里的文件只留在本机，Cloud Agent 读不到。User Rules 存在账号上，本地和云端都会加载。User Rules 不是文件，仓库里的 `~/Downloads/agent-skills/cursor/user-rules.md` 存一份「通用工作约束」的全文副本，两边要保持逐字一致。

`~/.cursor/skills/` 下的每个 skill 都是软链，指向仓库 `Muqian-Sun/agent-skills` 的本地克隆 `~/Downloads/agent-skills/cursor/skills/<name>`。改 skill 就是改这个仓库里的文件。Cloud Agent 按 User Rules 里的指令从这个仓库的 main 拉取 skill，所以改完要推上去，云端才拿得到。

这是 Claude Code 全局 `~/.claude/CLAUDE.md` 在 Cursor 里的对应物。本技能只改 Cursor 这边，不去改 `~/.claude/CLAUDE.md`。

## 什么时候沉淀

在一个项目里沉淀出经验之后，把其中**通用、可复用**的部分写回全局规则。写之前先过三道筛子：

- **换个项目也成立吗？** 只在这个项目里成立的约定，写进该仓库自己的 `AGENTS.md` / `.cursor/rules`，不进全局
- **还会再遇到吗？** 一次性的修复、偶发的环境问题，不沉淀
- **已经有了吗？** 先把现有规则读一遍：User Rules 用 `cursor-app-control` 的 `cursor_dialog`（`item: rule`、`scope: user`、`action: list`）列出，skill 读 `~/.cursor/skills/*/SKILL.md`。已有同类条目就合并或改写那一条，不另起一条说同一件事

## 放到哪里：按四类归位

| 经验属于 | 放在哪 | 怎么被读到 |
|---|---|---|
| **通用的**工作范式、踩过的坑、得出的经验 | User Rules 里「通用工作约束」那一条，开一个 `##` 子标签（已有合适的就加进去），子标签下分点写 | 每个会话常驻加载 |
| **特定语言的**坑和范式 | `~/.cursor/skills/<语言>-pitfalls/SKILL.md`（已有就追加）。frontmatter：`name` 与目录名一致，`paths` 写成该语言的文件模式（Python 用 `"**/*.py"`，Go 用 `"**/*.go"`），`description` 写明内容和触发条件。新建时在「通用工作约束」的「引用的文档」一节加一行 | 处理匹配文件时出现在可用列表里，相关时加载 |
| **和 shell、操作系统、命令行工具、批量改写文件有关的**坑 | `~/.cursor/skills/shell-pitfalls/SKILL.md`（已有就追加）。**不要设 `paths`**，`description` 写明触发条件 | 模型根据 description 判断相关后加载 |
| **特定的工作流程**（某一类任务从头到尾怎么做） | 写成一个 skill：`~/Downloads/agent-skills/cursor/skills/<name>/SKILL.md`，用 `install.sh --link` 挂进 `~/.cursor/skills/`，description 写清触发场景。「通用工作约束」里**不加引用** | skill 的 description 自动出现在可用列表里，命中场景时加载 |

分类拿不准时这样判断：**不分场景**都该遵守的，是通用的；**只在写某门语言时**才用得上的，是特定语言的；和 shell、操作系统、命令行工具有关、换一门语言还会遇到的，归 shell；描述的是**某一类任务完整怎么做**的，是工作流程。

**「在写某门语言时踩到的」不等于「这门语言专有的」。** 判据是：换一门语言还会不会遇到？会遇到，就不归那门语言。和 shell、操作系统、命令行工具、写文件工具有关的坑，归进 `shell-pitfalls`——不要因为是写 Go 时发现的就塞进 `go-pitfalls`，那样只有 Go 文件在上下文里才读得到，换成写 Python 照样会再踩一次。

## 怎么写

- 分点写，一点只讲一件事
- 写清楚**为什么**，不只写规则本身——知道原因，才能在没见过的场景里判断这条适不适用
- 写成能照着做的判据，不写"注意 xxx"这种没法执行的提醒
- **写进 `shell-pitfalls` 的条目要标明适用的系统**：本机是 macOS + zsh，Cloud Agent 的服务器是 Linux，同一条命令在两边的行为可能不同。每条开头标 `【macOS】`、`【Linux】` 或 `【macOS / Linux】`；行为取决于 shell 的，再标上 shell（zsh / bash / dash）。两边行为不同的写进同一条，分别写清各自的表现和通用做法
- **`shell-pitfalls` 的条目只在一边测过，就只写那一边**。标「实测」时写清在哪个系统上测的；另一边没测就写「Linux 未实测」或「macOS 未实测」，不要从一边推断另一边。本机有 docker，可以用本地的 Ubuntu 镜像实测 Linux 行为。容器默认以 root 运行，涉及权限、目录创建的要加 `--user 1000:1000`，否则 root 能建任意目录，会测出和真实环境不同的结果
- 新语言 skill 的 frontmatter 照已有的 `python-pitfalls` / `go-pitfalls` 写。`description` 用第三人称，写清做什么、什么时候用
- 改 User Rules 用 `cursor_dialog` 的 `update`：先 `list` 拿到「通用工作约束」的 `id`，`content` 传**改完后的全文**（整条替换，不是追加）。改完再 `list` 一遍，确认改动在、其余段落没丢；再把同样的全文写进 `cursor/user-rules.md`，提交并推送
- **新建 skill 建在仓库里**：在 `~/Downloads/agent-skills/cursor/skills/<name>/` 下建，再跑 `~/Downloads/agent-skills/cursor/install.sh --link` 把它挂进 `~/.cursor/skills/`。不要直接在 `~/.cursor/skills/` 下建普通目录——那样它不在仓库里，云端拿不到
- **改完 skill 提交并推送**：按 `git-workflow` 在 `~/Downloads/agent-skills` 里提交、推送 main
- **新增、删除或改名 skill 时**，同步改「通用工作约束」里「Cloud Agent 里的 skill」一节的列表——云端的 skill 不进 skill 列表，只能靠那张表按场景去读

## 改之前先给用户看

全局规则影响所有项目。把拟加或拟改的内容——归到哪一类、放在哪里、具体写什么——先给用户过目，确认后再写入。

新写的 skill 挂进 `~/.cursor/skills/` 后才会被加载，并且新开会话才生效。

## 反面模式

- ❌ 把项目专有的约定写进「通用工作约束」
- ❌ 只和某门语言有关的内容直接堆进「通用工作约束」
- ❌ 在写某门语言时踩到的环境坑（shell、操作系统、工具），归进了那门语言的 skill
- ❌ 给 `shell-pitfalls` 设了 `paths`——设了就只有匹配文件在上下文里才出现，跑命令时用不上
- ❌ 工作流程写成规则、再在「通用工作约束」里引用——那是 skill 的活：skill 的描述会自动出现在可用列表里
- ❌ 写进 `~/.cursor/rules/*.mdc`——只留在本机，Cloud Agent 读不到
- ❌ 在 `~/.cursor/skills/` 下直接建普通目录的 skill，或改完 skill 不推送——云端拿不到
- ❌ 只改了 User Rules 没更新 `cursor/user-rules.md`，或反过来——两份对不上，不知道哪份是对的
- ❌ `shell-pitfalls` 的条目不标 macOS / Linux，或者只在 macOS 上测过就写成两边通用
- ❌ 不查重，同一条经验换个说法又加一遍
- ❌ 没给用户看就改全局规则
- ❌ 去改 `~/.claude/CLAUDE.md`。那边由 Claude Code 自己的技能维护
