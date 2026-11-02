#!/usr/bin/env python3
"""Change text values in sce_sys/param.sfo (the game's title in the Vita3K list / Vita home screen).

The values are in text/param_sfo.tsv, one per line:  KEY <TAB> value   (# = comment)
e.g.  TITLE	Saki Zenkoku-hen Plus

    python3 tools/sfo.py show <game_dir>     list what is in the game's param.sfo

"build" in saki.py uses this automatically and writes build/sce_sys/param.sfo.
"""
import os, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TSV = os.path.join(ROOT, 'text', 'param_sfo.tsv')

def entries(d):
    if d[:4] != b'\0PSF': raise ValueError('not a param.sfo file')
    _, _, kt, dt, n = struct.unpack('<4sIIII', d[:20])
    for i in range(n):
        ko, fmt, ln, mx, do = struct.unpack('<HHIII', d[20 + 16 * i:36 + 16 * i])
        key = d[kt + ko:d.index(b'\0', kt + ko)].decode()
        yield i, key, fmt, ln, mx, dt + do

def show(game):
    d = open(sfo_src(game), 'rb').read()
    for i, key, fmt, ln, mx, off in entries(d):
        v = d[off:off + ln]
        print(f'{key:18} {v.rstrip(bytes(1)).decode("utf-8", "replace") if fmt == 0x204 else struct.unpack("<I", v)[0]}')

def load_values(path=TSV):
    vals = {}
    if os.path.exists(path):
        for line in open(path, encoding='utf-8'):
            line = line.rstrip('\r\n')
            if line.strip() and not line.startswith('#') and '\t' in line:
                k, v = line.split('\t', 1); vals[k.strip()] = v
    return vals

def apply(d, vals):
    """Return (new bytes, problems). Only text (utf-8) values can be changed."""
    out = bytearray(d); problems = []; seen = set()
    for i, key, fmt, ln, mx, off in entries(d):
        if key not in vals: continue
        seen.add(key)
        b = vals[key].encode('utf-8') + b'\0'
        if fmt != 0x204: problems.append(f'{key} is not a text value'); continue
        if len(b) > mx: problems.append(f'{key}: "{vals[key]}" is {len(b) - 1} bytes, max {mx - 1}'); continue
        out[off:off + mx] = b + bytes(mx - len(b))
        struct.pack_into('<I', out, 20 + 16 * i + 4, len(b))
    for k in set(vals) - seen: problems.append(f'{k} is not in this param.sfo')
    return bytes(out), problems

def sfo_src(game):
    p = os.path.join(game, 'sce_sys', 'param.sfo')
    return p + '.orig' if os.path.exists(p + '.orig') else p

if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == 'show': show(os.path.expanduser(a[1]))
    else: sys.exit(__doc__)
