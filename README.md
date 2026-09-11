# claude-skills

我自用的 Claude Code Skill 集合。每个 skill 一个目录，放在 `skills/` 下。

## 目录

| Skill | 干什么用的 |
|---|---|
| [`map-system`](skills/map-system/SKILL.md) | 划定一个系统由哪些仓库 / 子项目组成：产出系统组成表（谁属于这个系统、哪些读得到、本次聚焦哪一块），再交棒给 `explain-project` |
| [`explain-project`](skills/explain-project/SKILL.md) | 带新人深入**一个**仓库：按「项目定位 → 代码地图 → 对外接口 → 分层架构 → 核心链路 → 数据模型与黑话 → 一次真实请求 → 技术方案 → 关键源码」分阶段讲透 |

## 安装

两个 skill 配套使用：`map-system` 先划范围，`explain-project` 再深入其中一个仓。只装一个也能用——已知边界时可以直接用 `explain-project`。

装单个 skill：

```bash
cp -r skills/explain-project ~/.claude/skills/
```

全装：

```bash
cp -r skills/* ~/.claude/skills/
```

两点实测结论：

- `~/.claude/skills/` 下的**符号链接会被正常发现**，所以本地开发可以 `ln -s "$PWD/skills/explain-project" ~/.claude/skills/explain-project`，改仓库即改生效的 skill
- skill 的**正文是会话启动时的快照**（description 会在会话内刷新，正文不会），所以改完 SKILL.md 要**新开一个会话**才真正生效

## 新增一个 skill

1. 建目录 `skills/<name>/`，写 `SKILL.md`
2. frontmatter 里 `description` 要写清**什么时候该触发**——这是模型唯一的选用依据，写模糊了就不会被用上；`name` 按约定与目录名保持一致（`validate` 不检查这条，实测名字对不上也能过）
3. 在上面的目录表里加一行
4. `claude plugin validate .` 过一遍再提交

## 打包成 .skill

```bash
cd skills && zip -r ../<name>.skill <name>
```

`.skill` 包是产物，不进版本库——单一真相源是 `skills/<name>/SKILL.md`。
