# explain-project

一个 Claude Code Skill：面向研发新人的项目导览。

给刚接手陌生仓库的人用——按「项目定位 → 代码地图 → 对外接口 → 分层架构 → 核心链路 → 数据模型与黑话 → 一次真实请求 → 技术方案 → 关键源码」的顺序分阶段讲，而不是甩一份写给老员工看的架构文档。

技能全文见 [`explain-project/SKILL.md`](explain-project/SKILL.md)。

## 安装

拷进个人 skills 目录即可：

```bash
cp -r explain-project ~/.claude/skills/
```

已安装的副本是独立的一份，仓库更新后需要重新拷贝才生效；skill 在会话启动时加载，装完要新开一个会话。

## 打包成 .skill

```bash
zip -r explain-project.skill explain-project
```

`.skill` 包是产物，不进版本库——单一真相源是 `explain-project/SKILL.md`。
