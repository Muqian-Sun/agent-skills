#!/usr/bin/env python3
"""按日期范围，从 Claude Code 会话记录里抽出用户说过的话和选择题里的决策。

只读顶层 <projects-dir>/*/*.jsonl；子 agent 的记录在子目录里，不读。

fail-closed：
- 文件中间有解析不了的行、user 事件缺时间戳、遇到没见过的 content 形态，都记为错误，
  最后打到 stderr，退出码 2。能解析的部分照常输出，但不能当成全量。
- 只容忍每个文件的最后一行不完整：正在进行的会话会出现这种情况。
"""
import argparse
import glob
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta

# harness 注入到 user 事件里的内容，不是用户本人输入
HARNESS_PREFIXES = (
    "<task-notification>", "<command-name>", "<command-message>", "<command-args>",
    "<local-command-stdout>", "<local-command-stderr>", "<local-command-caveat>",
    "<system-reminder>",
)
KNOWN_BLOCKS = {"text", "tool_result", "image", "document"}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--since", required=True, type=date.fromisoformat, help="起始日期（含），本地时区，YYYY-MM-DD")
    p.add_argument("--until", type=date.fromisoformat, default=date.today(), help="结束日期（含），默认今天")
    p.add_argument("--cwd", help="只看工作目录包含这个关键字的会话")
    p.add_argument("--projects-dir", default=os.path.expanduser("~/.claude/projects"))
    p.add_argument("--settings-file", default=os.path.expanduser("~/.claude/settings.json"),
                   help="读取 cleanupPeriodDays，用于提示记录可能已被清理")
    p.add_argument("--max-chars", type=int, default=2000,
                   help="单条用户输入的截断长度（默认 2000，拍的，只为防止粘贴的大段内容淹没输出）")
    return p.parse_args()


def retention_days(settings_file):
    try:
        with open(settings_file, encoding="utf-8") as fh:
            v = json.load(fh).get("cleanupPeriodDays")
    except FileNotFoundError:
        return 30, "默认值"
    if isinstance(v, int) and v >= 1:
        return v, settings_file
    if v is None:
        return 30, "默认值"
    raise SystemExit(f"错误：{settings_file} 里的 cleanupPeriodDays 不是正整数：{v!r}")


def user_text(event):
    content = (event.get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        kinds = {b.get("type") for b in content if isinstance(b, dict)}
        unknown = kinds - KNOWN_BLOCKS
        if unknown:
            raise ValueError(f"没见过的 content 块类型 {sorted(unknown)}")
        parts = []
        for b in content:
            if b.get("type") == "text":
                parts.append(b.get("text", ""))
            elif b.get("type") in ("image", "document"):
                parts.append(f"[{b['type']}]")
        return "\n".join(parts) if parts else None
    raise ValueError(f"没见过的 content 形态 {type(content).__name__}")


def main():
    args = parse_args()
    if args.since > args.until:
        raise SystemExit("错误：--since 晚于 --until")

    keep, source = retention_days(args.settings_file)
    oldest_kept = date.today() - timedelta(days=keep)
    if args.since < oldest_kept:
        print(f"提示：会话记录保留 {keep} 天（{source}），{oldest_kept} 之前的记录可能已被清理。", file=sys.stderr)

    files = sorted(glob.glob(os.path.join(args.projects_dir, "*", "*.jsonl")))
    if not files:
        raise SystemExit(f"错误：{args.projects_dir} 下没有找到任何会话记录")

    sessions = defaultdict(list)  # (cwd, session_id) -> [(time, kind, text)]
    errors = []

    for path in files:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        while lines and not lines[-1].strip():
            lines.pop()
        for i, line in enumerate(lines):
            where = f"{path}:{i + 1}"
            try:
                e = json.loads(line)
            except json.JSONDecodeError as ex:
                if i == len(lines) - 1:
                    continue  # 进行中的会话，最后一行可能还没写完
                errors.append(f"{where} JSON 解析失败：{ex}")
                continue
            if e.get("type") != "user" or e.get("isSidechain"):
                continue
            ts = e.get("timestamp")
            if not ts:
                errors.append(f"{where} user 事件缺 timestamp")
                continue
            t = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
            if not (args.since <= t.date() <= args.until):
                continue
            cwd = e.get("cwd") or "(未知目录)"
            if args.cwd and args.cwd not in cwd:
                continue
            key = (cwd, e.get("sessionId") or os.path.basename(path)[: -len(".jsonl")])

            result = e.get("toolUseResult")
            if isinstance(result, dict) and isinstance(result.get("answers"), dict):
                for q, a in result["answers"].items():
                    sessions[key].append((t, "决策", f"{q} → {a}"))
                continue
            if result is not None or e.get("isMeta"):
                continue  # 其他工具结果、skill 正文等注入内容

            try:
                text = user_text(e)
            except ValueError as ex:
                errors.append(f"{where} {ex}")
                continue
            if not text or not text.strip() or text.lstrip().startswith(HARNESS_PREFIXES):
                continue
            if len(text) > args.max_chars:
                text = text[: args.max_chars] + f"…[截断，原文 {len(text)} 字]"
            sessions[key].append((t, "用户", text))

    by_cwd = defaultdict(list)
    for (cwd, sid), items in sessions.items():
        items.sort(key=lambda x: x[0])
        by_cwd[cwd].append((sid, items))

    n_user = sum(1 for v in sessions.values() for x in v if x[1] == "用户")
    n_dec = sum(1 for v in sessions.values() for x in v if x[1] == "决策")
    print(f"# 会话素材 {args.since} ~ {args.until}")
    print(f"\n共 {len(by_cwd)} 个项目目录、{len(sessions)} 个会话、{n_user} 条用户输入、{n_dec} 条决策\n")
    for cwd in sorted(by_cwd, key=lambda c: min(s[1][0][0] for s in by_cwd[c])):
        print(f"## {cwd}\n")
        for sid, items in sorted(by_cwd[cwd], key=lambda s: s[1][0][0]):
            print(f"### 会话 {sid[:8]} · {items[0][0]:%Y-%m-%d %H:%M} → {items[-1][0]:%Y-%m-%d %H:%M}\n")
            for t, kind, text in items:
                print(f"- {t:%m-%d %H:%M} {kind}：" + text.replace("\n", " ⏎ "))
            print()

    if errors:
        print(f"\n错误：{len(errors)} 处记录解析不了，上面的结果不全：", file=sys.stderr)
        for err in errors:
            print("  " + err, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
