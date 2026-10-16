#!/usr/bin/env bash
# Saki Zenkoku-hen Plus (PCSG00908, v2.01) - English patch installer for Linux/macOS.
#
#   ./apply.sh <path-to-DATA-folder>              patch the game in place (backs up originals as *.orig)
#   ./apply.sh <path-to-DATA-folder> <out-dir>    leave the game alone, write patched files to <out-dir>
#                                                 (use this for rePatch on a real Vita)
#   ./apply.sh --restore <path-to-DATA-folder>    undo: put the *.orig backups back
#
# Needs: xdelta3 (Arch: pacman -S xdelta3, Debian/Ubuntu: apt install xdelta3, macOS: brew install xdelta)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

if [ "${1:-}" = "--restore" ]; then
    DATA="${2:?usage: ./apply.sh --restore <DATA folder>}"
    while read -r name orig new; do
        if [ -f "$DATA/$name.orig" ]; then cp -f "$DATA/$name.orig" "$DATA/$name"; echo "restored $name"; fi
    done < "$HERE/files.txt"
    exit 0
fi

DATA="${1:?usage: ./apply.sh <DATA folder> [output folder]}"
OUT="${2:-}"
command -v xdelta3 >/dev/null || { echo "xdelta3 is not installed (see the top of this script)"; exit 1; }
sha() { sha1sum "$1" 2>/dev/null | cut -d' ' -f1 || shasum "$1" | cut -d' ' -f1; }

echo "Checking your game files ..."
declare -A BASE
while read -r name orig new; do
    t="$DATA/$name"
    if [ -f "$t.orig" ]; then b="$t.orig"; else b="$t"; fi
    [ -f "$b" ] || { echo "MISSING: $t"; exit 1; }
    h="$(sha "$b")"
    if [ "$h" != "$orig" ]; then
        echo "WRONG VERSION: $name does not match Saki Zenkoku-hen Plus v2.01 (sha1 $h)"
        echo "Nothing was changed."; exit 1
    fi
    BASE[$name]="$b"
done < "$HERE/files.txt"

[ -n "$OUT" ] && mkdir -p "$OUT"
while read -r name orig new; do
    b="${BASE[$name]}"; t="$DATA/$name"
    if [ -z "$OUT" ] && [ "$b" = "$t" ]; then cp -f "$t" "$t.orig"; b="$t.orig"; fi
    dest="${OUT:-$DATA}/$name"
    echo "patching $name ..."
    xdelta3 -d -f -s "$b" "$HERE/patches/$name.xdelta" "$dest.tmp"
    if [ "$(sha "$dest.tmp")" != "$new" ]; then rm -f "$dest.tmp"; echo "PATCH FAILED for $name"; exit 1; fi
    mv -f "$dest.tmp" "$dest"
done < "$HERE/files.txt"
echo "Done! The English patch is installed."
