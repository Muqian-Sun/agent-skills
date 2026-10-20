#!/usr/bin/env bash
# 把 cursor/skills/ 下的 skill 装进 Cursor 的个人 skill 目录。
#   install.sh          复制（Cloud Agent 用）：同名的普通目录会被替换
#   install.sh --link   软链（本机用）：改仓库即改生效的 skill
# 目标目录默认 ~/.cursor/skills，可用 CURSOR_SKILLS_DIR 改。
set -euo pipefail

mode=copy
case "${1:-}" in
  "") ;;
  --link) mode=link ;;
  *) echo "usage: $0 [--link]" >&2; exit 2 ;;
esac

src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skills"
dst="${CURSOR_SKILLS_DIR:-$HOME/.cursor/skills}"
mkdir -p "$dst"

skipped=0
for dir in "$src"/*/; do
  dir="${dir%/}"
  name="$(basename "$dir")"
  target="$dst/$name"
  if [ "$mode" = link ]; then
    if [ -L "$target" ]; then
      rm "$target"
    elif [ -e "$target" ]; then
      echo "skip $name: $target 已存在且不是软链，先移走再重跑" >&2
      skipped=$((skipped + 1))
      continue
    fi
    ln -s "$dir" "$target"
  else
    if [ -L "$target" ]; then
      echo "skip $name: $target 是软链，复制会写回它指向的目录" >&2
      skipped=$((skipped + 1))
      continue
    fi
    rm -rf "$target"
    cp -R "$dir" "$target"
  fi
  echo "$mode $name -> $target"
done

if [ "$skipped" -gt 0 ]; then
  echo "$skipped 个 skill 被跳过" >&2
  exit 1
fi
