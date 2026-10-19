#!/usr/bin/env python3
"""Translate the text that lives inside the game program (eboot.bin).

Some text is not an image: the music-list names, the save-data messages, the online
lobby messages and so on are UTF-8 strings inside eboot.bin, drawn by the game with
its own font. The translations are in text/eboot.tsv (one string per line):

    japanese <TAB> english <TAB> optional note

Write a line break as \\n. Leave the English empty to keep the Japanese.
Each English string must fit in the space of the Japanese one (UTF-8 bytes: Japanese
characters take 3 bytes each, English letters 1, so this is rarely a problem) plus
any unused zero bytes after it. %s / %d codes must stay the same and in the same order.

    python3 tools/eboot.py check <game_dir>    show which lines are found and how much room they have
    python3 tools/eboot.py dump  <game_dir>    list every Japanese string -> work/eboot_strings.tsv
                                               (to find new text to translate)

"build" in saki.py uses this automatically: the translated eboot.bin goes to build/eboot.bin.
Works only on a decrypted eboot.bin (as Vita3K and dumpers like Mai leave it).
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TSV = os.path.join(ROOT, 'text', 'eboot.tsv')
FMT = re.compile(r'%[-+ #0]*\d*(?:\.\d+)?[a-zA-Z]')

def unesc(s): return s.replace('\\n', '\n').replace('\\t', '\t')
def esc(s): return s.replace('\t', '\\t').replace('\n', '\\n')

def load_rows(path=TSV):
    rows = []
    if not os.path.exists(path): return rows
    for k, line in enumerate(open(path, encoding='utf-8'), 1):
        line = line.rstrip('\r\n')
        if not line.strip() or line.startswith('#'): continue
        p = line.split('\t')
        ja, en = unesc(p[0]), unesc(p[1]) if len(p) > 1 else ''
        if en.strip(): rows.append((k, ja, en))
    return rows

def find(data, ja):
    """Every place where the whole string `ja` is stored (with its terminating zero)."""
    pat = ja.encode('utf-8') + b'\0'; out = []; i = data.find(pat)
    while i >= 0:
        prev = data[i - 1] if i else 0
        # must be the start of a string: after a zero byte, or right after a pointer table
        if prev == 0 or (prev == 0x81 and i % 4 == 0): out.append(i)
        i = data.find(pat, i + 1)
    return out

def room(data, off, n):
    """Bytes available for a string at off whose original length is n (keeps one zero at the end)."""
    e = off + n; z = 0
    while e + z < len(data) and data[e + z] == 0: z += 1
    return n + z - 1

def apply(data, rows, verbose=True):
    """Return (patched bytes, list of problems)."""
    out = bytearray(data); problems = []; done = 0
    for k, ja, en in rows:
        if FMT.findall(ja) != FMT.findall(en):
            problems.append(f'line {k}: %-codes differ ({FMT.findall(ja)} vs {FMT.findall(en)}): {esc(en)}'); continue
        offs = find(data, ja)
        if not offs:
            problems.append(f'line {k}: not found in eboot.bin: {esc(ja)}'); continue
        b = en.encode('utf-8'); n = len(ja.encode('utf-8'))
        for o in offs:
            r = room(data, o, n)
            if len(b) > r:
                problems.append(f'line {k}: "{esc(en)}" is {len(b)} bytes, only {r} fit'); break
        else:
            for o in offs:
                r = room(data, o, n)
                out[o:o + r + 1] = b + b'\0' * (r + 1 - len(b))
            done += 1
    if verbose: print(f'  eboot.bin: {done} of {len(rows)} strings translated')
    return bytes(out), problems

def eboot_src(game):
    p = os.path.join(game, 'eboot.bin')
    return p + '.orig' if os.path.exists(p + '.orig') else p

def check(game):
    data = open(eboot_src(game), 'rb').read()
    for k, ja, en in load_rows():
        offs = find(data, ja); n = len(ja.encode('utf-8'))
        r = min((room(data, o, n) for o in offs), default=0)
        b = len(en.encode('utf-8'))
        st = 'NOT FOUND' if not offs else ('TOO LONG' if b > r else 'ok')
        print(f'{st:9} {b:3}/{r:<3} x{len(offs)}  {esc(ja)}  ->  {esc(en)}')
    _, problems = apply(data, load_rows(), verbose=False)
    for p in problems: print('PROBLEM', p)

def dump(game):
    data = open(eboot_src(game), 'rb').read()
    seen, rows = set(), []
    for m in re.finditer(rb'[\xe3-\xe9][\x80-\xbf]{2}', data):
        s = m.start()
        while s > 0 and data[s - 1] != 0 and m.start() - s < 400: s -= 1
        if s in seen: continue
        seen.add(s); e = data.index(b'\0', m.start())
        try: t = data[s:e].decode('utf-8')
        except UnicodeDecodeError: continue
        if not re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', t): continue
        rows.append(f'{s:#08x}\t{room(data, s, e - s)}\t{esc(t)}')
    os.makedirs(os.path.join(ROOT, 'work'), exist_ok=True)
    out = os.path.join(ROOT, 'work', 'eboot_strings.tsv')
    open(out, 'w', encoding='utf-8').write('offset\troom_bytes\tjapanese\n' + '\n'.join(rows) + '\n')
    print(f'{len(rows)} strings -> {out}  (many are debug menus that players never see)')

if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == 'check': check(os.path.expanduser(a[1]))
    elif len(a) == 2 and a[0] == 'dump': dump(os.path.expanduser(a[1]))
    else: sys.exit(__doc__)
