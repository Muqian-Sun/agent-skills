---
name: git-workflow
description: Git 协作规范：分支怎么建、commit 怎么写、PR 怎么提和描述、PR 用什么方式合入、合入后怎么同步 main 并清理分支和 worktree、code review 看什么、分支和主干冲突怎么解、main 能不能推。凡是要建分支、写 commit message、提 PR、写 PR 描述、合入 PR、合入后清理分支和 worktree、做 code review、处理分支与主干的冲突、推送代码时，务必使用本技能——哪怕只是"帮我提交一下 / 推上去 / 开个 PR / 合入 / 删掉合过的分支"。英文的 "commit this" / "open a PR" / "merge this PR" / "clean up merged branches" / "review this PR" / "rebase onto main" / "push" 同样适用。仓库自己有约定（PR 模板、CONTRIBUTING、历来的提交方式）时以仓库为准，本技能补足仓库没写的部分。
---

# Git 协作规范

来源：某团队内部的 Git 规范文档。原文以 Go 后端为背景，这里已做通用化改写；标注「原文」的地方是 Go 专有，换语言时按项目实际替换。

## 先看仓库自己的约定

这套规范来自一个团队的约定，不是每个仓库都这么做。动手前先看仓库里有没有：

- `CONTRIBUTING.md`、`.github/PULL_REQUEST_TEMPLATE.md` 这类明文约定
- `git log` 里历来的提交方式：commit message 是什么格式、走的是分支 + PR 还是直接提交到 main

**仓库有约定就以仓库为准**，本技能只补仓库没写的部分。比如个人仓库一直直接提交到 main，就不要硬套下面的分支模型。

## 分支模型

类 GitHub Flow 的轻量模型：

- `main` — 永远保持可发布状态。
- `feat/<desc>` — 新功能。示例 `feat/add-user-service`。
- `fix/<desc>` — Bug 修复。示例 `fix/missing-token-check`。
- `hotfix/<desc>` — 线上紧急问题修复。

## 推送 main 的边界

- **任何仓库都绝不强推 main / master**：`--force` 和 `--force-with-lease` 都不行。main 的历史一旦被改写，所有基于它的分支和部署都会受牵连。
- **团队仓库、共享仓库绝不直接推 main**，一律走分支 + PR。
- **个人仓库**：用户明确要求时，可以对 main 做普通推送。推之前先 `git fetch`，用 `git merge-base --is-ancestor origin/main main` 确认是快进；不是快进就停下来问，不要强推。

分不清是团队仓库还是个人仓库时，**按团队仓库处理**。只有 remote 在用户个人账号名下、并且没有其他协作者，才算个人仓库。

## 分支与主干冲突：只用 rebase

- **只用 rebase**，不要把主干 merge 进特性分支。merge 会在特性分支上留下一串合并提交，PR 的历史变脏，review 时很难看清到底改了什么。
- rebase 之后随之而来的 `git push --force-with-lease` **是被授权的**，不用为此停下来问——这一条覆盖默认的「绝不 force-push」。
- **边界写死**：只对**自己的特性分支**、只用 `--force-with-lease`；**绝不用 `--force`，绝不改别人的分支**。`--force-with-lease` 在远端已被别人推了新提交时会拒绝推送，`--force` 会直接把别人的提交覆盖掉。
- 仓库明确要求保留 merge commit 的，以仓库为准。

## Commit 规范

Conventional Commits 扩展版：

```
<type>(<scope>): <short summary>

<body>

<footer>
```

body 用短横线逐条列出具体改动点。示例：

```
feat(videos): 添加模型ID有效性校验

在创建和Remix视频任务时，增加对模型ID的存在性验证，
防止使用不存在的模型导致后续处理失败。

- VideosCreateAPI: 在任务类型判断前校验模型ID
- VideosRemixAPI: 在参数验证前校验原视频模型ID
```

开发过程中保持小粒度 commit：尽可能原子，一个 commit 完成一个相对独立的修改。

## PR 流程

1. 建分支：`git checkout -b feat/add-user-service`
2. 小粒度原子 commit
3. 推远程：`git push origin feat/add-user-service`
4. 提 PR 前 checklist：
   - 本地已跑通项目构建
   - 单测（如有）已通过
   - 配置文件无敏感信息
   - 变更内容合理拆分 commit
   - 代码通过 lint（原文：`go vet`；前端项目换成对应的 eslint / tsc 等）
5. PR 标题同样遵循 commit 规范：`feat(user): 新增用户查询 API`

## 合入 PR：只用 squash 或 rebase，不用 merge commit

- **任何仓库都不用 merge commit 合入**，`gh pr merge` 不带 `--merge`。只用 `--squash` 或 `--rebase`。
- **同目录 `local.md` 里列出的仓库一律 squash**：`gh pr merge <编号> --squash`。按远程仓库判断，不看本地目录名和 worktree 名。`local.md` 不进版本库，没有这个文件就当名单为空。
- **其他仓库按 PR 里的提交选**：
  - 每个提交都是原子的、message 符合上面的 commit 规范、单独留在 main 上有意义 → `--rebase`。
  - 有 `wip`、`fix typo`、「按 review 修改」这类过程提交，或者整个 PR 本来就是一件事 → `--squash`，squash 后的标题和 body 按 commit 规范写。
- 合入前用 `gh repo view --json squashMergeAllowed,rebaseMergeAllowed` 看仓库允许哪种。选中的那种被禁用了就换另一种，两种都禁用就停下来问，不要退回 merge commit。
- **不要从 git 历史推断合入方式**。main 上已有的 merge commit 不代表应该继续用 merge commit。2026-10-09 合一个团队仓库的 PR 时只看了 main 最近 3 个提交，误判成 merge commit。
- 这条是用户定的，Confluence 原文里没有。

## 合入之后：同步 main，删掉分支和 worktree

PR 合入后马上收尾，不要等用户提醒。这条是用户定的，Confluence 原文里没有。

1. **确认真的合入了**：`gh pr view <编号> --json state,headRefName,headRefOid`，`state` 是 `MERGED` 才往下走。
2. **同步本地 main**：`git fetch --prune origin`，切到 main，`git merge --ff-only origin/main`。
   - 不能快进时**不要直接 `reset --hard`**。先 `git log origin/main..main` 看本地多出来的提交，逐个确认内容已经在 `origin/main` 里（`git diff <提交> origin/main -- <它改过的文件>` 只剩后来的修改），都在才 `git reset --hard origin/main`；有没进去的就停下来问。2026-10-17 travel-buddy 的本地 main 是一个孤立的根提交，内容和远端根提交相同，核对后才重置。
   - main 没有上游的，顺手 `git branch -u origin/main main`。
3. **删 worktree**：`git worktree remove <路径>`，再 `git worktree prune`。有未提交改动时 `remove` 会拒绝，**不要加 `--force`**，停下来问。要删的分支正检出在当前目录时，先切回 main 再删。
4. **删本地分支**：`git branch -d <分支>`。
   - squash 和 rebase 合入都会在 main 上生成新的提交，原分支的提交不在 main 的祖先里，`-d` 会拒绝。这时核对本地分支头等于 PR 的 `headRefOid`，相等才用 `-D`；不相等说明合入后又有新提交，停下来问。
5. **删远端分支**：`git push origin --delete <分支>`，或合入时直接加 `--delete-branch`（如 `gh pr merge <编号> --squash --delete-branch`）。GitHub 开了自动删除的话远端已经没了，`fetch --prune` 会清掉本地的远端跟踪引用。
6. **核对**：`git worktree list`、`git branch -vv`、`git branch -r`、`git config --get-regexp '^branch\.'`，确认分支、worktree、分支配置段都没了，main 跟踪 `origin/main` 且没有 ahead / behind。

Cursor 沙箱不让写 `.git/config`：`git branch -u` 会失败，`git branch -d` 删掉了分支却留下 `branch.<名>` 配置段，只打一行 warning、退出码还是 0（2026-10-17 实测）。这两步要用完整权限跑，残留的配置段用 `git config --remove-section branch.<名>` 清掉。

## PR 描述五段式

1. **变更内容（What）** — 本 PR 实现了什么功能 / 修复了什么问题
2. **变更原因（Why）** — 背景、上下文
3. **变更方式（How）** — 技术方案；有无影响现有模块；数据迁移 / 兼容性问题
4. **测试方式（Test plan）** — 如何验证；覆盖哪些场景
5. **相关 Issue / PR（Links）** — `Closes #123`、`Ref #120`

仓库里若已有 `.github/PULL_REQUEST_TEMPLATE.md`，以仓库模板为准，缺失的段落按上面补齐。

## Review 标准

- **代码质量** — 是否可读；是否遵循该语言的最佳实践（原文指 Go）；有无多余代码、重复逻辑
- **设计合理性** — 分层是否符合当前项目结构；是否引入不必要依赖
- **安全性** — 用户输入校验；权限校验（如有）；敏感数据未暴露
- **性能** — 有无明显的 N+1、内存泄漏、并发泄漏（原文：Goroutine 泄漏）；是否有必要加缓存或优化
- **文档 & 注释** — 新接口是否更新接口文档；代码逻辑是否提供注释
