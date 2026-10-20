---
name: shell-pitfalls
description: Shell 与本机环境（macOS / Linux、zsh / bash / dash、命令行工具、批量改写文件）的坑，条目按系统和 shell 标注。跑 shell 命令、写 shell 脚本、批量改写文件时使用。
---

# Shell 与本机环境：踩过的坑与范式

触发条件：跑 shell 命令、写 shell 脚本、批量改写文件时。

本机是 macOS + zsh，Cloud Agent 的服务器是 Ubuntu 24.04 + bash（Cloud Agent 里实测 `SHELL=/bin/bash`）。每条开头标适用的系统，行为取决于 shell 的再标 shell。「实测」写明在哪测的：macOS 指本机（zsh 5.9、bash 3.2、perl 5.34），Linux 指 Docker 里的 Ubuntu 24.04（bash 5.2、dash、perl 5.38）。这些坑和用哪门语言无关——最初是写 Go 时踩到的，换一门语言照样会遇到。

- **【macOS / Linux】`timeout` 两边不一样**。macOS 没有 `timeout` / `gtimeout`（macOS 实测）；Ubuntu 自带 coreutils 的 `/usr/bin/timeout`，超时退出码 124（Linux 实测）。要两边都能跑，就用被调用程序自带的超时参数，比如 `go test -timeout 60s`，不要依赖外部 `timeout`。
- **【macOS / Linux】未加引号的变量拆不拆分取决于 shell**。zsh 不拆分：`P="./a ./b"; go test $P` 会把整串当成一个参数，报 setup failed（macOS 实测，踩过一次，整轮验证结果作废）；bash 会按空格拆分，还会展开通配符，`Q="x*"; f $Q` 传进去的是匹配到的文件名（Linux 实测；macOS 的 bash 未实测）。两边通用的做法：列表一律用数组，`P=(./a ./b); go test "${P[@]}"`，zsh 和 bash 都支持。
- **【macOS / Linux】脚本里 `kill $(jobs -p)` 在 zsh 和 dash 下杀不掉进程**。zsh（macOS 实测）和 dash（Linux 上的 `sh`，实测）里 `$(jobs -p)` 是空的，`kill` 报参数不够，后台进程照跑，`wait` 永远卡住；bash 里能拿到 PID 并杀掉（macOS bash 3.2、Linux bash 5.2 都实测过）。zsh 直接跑 `jobs -p`（不放进 `$()`）输出的是 `[1]  + 24682 running ...` 这种任务行，也不是纯 PID。两边通用的做法：后台进程一律 `cmd & pids+=($!)` 记下来。**不要用死循环制造 CPU 负载来"模拟繁忙"**：踩过一次，8 个死循环跑了 22 分钟没人收。
- **【macOS / Linux】用 perl 批量改含中文的源码，要 `perl -CSD -Mutf8`**。只写 `-CSD` 时输入按字符解码、脚本里的中文却还是字节，一处都匹配不上，而且不报错（macOS perl 5.34、Linux perl 5.38 实测结果相同）。改完 `grep -c` 数一遍替换结果。
- **【macOS】写文件的工具会把 `\uXXXX` 转义替换成对应的字符**（macOS 上的会话里踩到两次；Linux 未实测）。运行输出完全一样，测试抓不住，只有和原文件 grep 比对才发现。含转义的源码写完要**数一遍出现次数**，或者用 perl 按字节写。
