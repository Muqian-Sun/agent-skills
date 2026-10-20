# agent-skills

我自用的 AI 编程助手 Skill 集合，按产品分目录：

```text
claude/skills/<name>/SKILL.md   Claude Code 版
cursor/skills/<name>/SKILL.md   Cursor 版
cursor/install.sh               Cursor 版的安装脚本
```

同名 skill 在各产品下各自独立维护，内容可以不一样（比如 `git-workflow`）。

## Claude Code

| Skill | 干什么用的 |
|---|---|
| [`map-system`](claude/skills/map-system/SKILL.md) | 划定一个系统由哪些仓库 / 子项目组成：产出系统组成表（谁属于这个系统、哪些读得到、本次聚焦哪一块），再交棒给 `explain-project` |
| [`explain-project`](claude/skills/explain-project/SKILL.md) | 带新人深入**一个**仓库：按「项目定位 → 代码地图 → 对外接口 → 分层架构 → 核心链路 → 数据模型与黑话 → 一次真实请求 → 技术方案 → 关键源码」分阶段讲透 |
| [`new-project-workflow`](claude/skills/new-project-workflow/SKILL.md) | 从零开发一个新系统的标准工作流：需求 → 产品 → 架构 → 方案，每一步与用户确认后才写代码 |
| [`sediment-to-claude-md`](claude/skills/sediment-to-claude-md/SKILL.md) | 把项目里得出的通用经验沉淀进全局 CLAUDE.md，按通用 / 特定语言 / 工作流程三类归位 |
| [`git-workflow`](claude/skills/git-workflow/SKILL.md) | Git 协作规范：分支模型、commit、PR、review，以及 rebase 与推送 main 的边界 |
| [`mine-achievements`](claude/skills/mine-achievements/SKILL.md) | 从日常工作里挖简历产出：平时把需求、取舍、坑、bug、优化攒进素材库，需要时从会话记录和 git 提交提炼成带证据的 bullet |

### 安装

两个 skill 配套使用：`map-system` 先划范围，`explain-project` 再深入其中一个仓。只装一个也能用——已知边界时可以直接用 `explain-project`。

装单个 skill：

```bash
cp -r claude/skills/explain-project ~/.claude/skills/
```

全装：

```bash
cp -r claude/skills/* ~/.claude/skills/
```

两点实测结论：

- `~/.claude/skills/` 下的**符号链接会被正常发现**，所以本地开发可以 `ln -s "$PWD/claude/skills/explain-project" ~/.claude/skills/explain-project`，改仓库即改生效的 skill
- skill 的**正文是会话启动时的快照**（description 会在会话内刷新，正文不会），所以改完 SKILL.md 要**新开一个会话**才真正生效

### 新增一个 skill

1. 建目录 `claude/skills/<name>/`，写 `SKILL.md`
2. frontmatter 里 `description` 要写清**什么时候该触发**——这是模型唯一的选用依据，写模糊了就不会被用上；`name` 按约定与目录名保持一致（`validate` 不检查这条，实测名字对不上也能过）
3. 在上面的目录表里加一行
4. `claude plugin validate --strict claude` 过一遍再提交（不加 `--strict` 时缺 frontmatter 只报警告、退出码仍是 0）

### 打包成 .skill

```bash
cd claude/skills && zip -r ../../<name>.skill <name>
```

`.skill` 包是产物，不进版本库——单一真相源是 `claude/skills/<name>/SKILL.md`。

## Cursor

| Skill | 干什么用的 |
|---|---|
| `explain-project`、`map-system`、`new-project-workflow`、`git-workflow` | 与 Claude Code 同名 skill 对应的 Cursor 版 |
| [`sediment-to-rules`](cursor/skills/sediment-to-rules/SKILL.md) | 把通用经验沉淀进 Cursor 的 User Rules 和 `*-pitfalls` skill |
| [`python-pitfalls`](cursor/skills/python-pitfalls/SKILL.md) | Python 的坑与范式，`paths: "**/*.py"` |
| [`go-pitfalls`](cursor/skills/go-pitfalls/SKILL.md) | Go 的坑与范式，`paths: "**/*.go"` |
| [`shell-pitfalls`](cursor/skills/shell-pitfalls/SKILL.md) | Shell 与本机环境的坑，条目按 macOS / Linux 标注 |

### 安装

本机用软链安装，改仓库即改生效的 skill（`~/.cursor/skills` 下已有同名普通目录时会跳过并以退出码 1 结束，先移走再重跑）：

```bash
cursor/install.sh --link
```

Cloud Agent 里用复制安装：

```bash
git clone --depth 1 https://github.com/Muqian-Sun/agent-skills /tmp/agent-skills
bash /tmp/agent-skills/cursor/install.sh
```

Cloud Agent 启动后才装上的 skill 不会进它的 skill 列表，要靠 User Rules 里的指令让它按场景去读 `~/.cursor/skills/<name>/SKILL.md`。按 Cursor 3.25.9 的代码，「Sync Skills for Cloud Agents」搬运 skill 时只处理普通目录、跳过软链，所以软链安装的 skill 不会被它同步。
