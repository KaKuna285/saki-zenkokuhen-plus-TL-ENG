#!/usr/bin/env python3
"""QPK/QPI archive tool for Saki Zenkoku-hen Plus (PCSG00908, PS Vita).

Format (reverse-engineered):
  QPI  header 0x14 bytes: 'QPI\\0', u32 count, 8-byte build timestamp, u32 0
       then count * (u32 offset, u32 size|flags), then (u32 end_of_data, u32 0).
       flags: 0x80000000 = empty slot (directory marker), 0x40000000 = CZL-compressed.
       size = UNCOMPRESSED size. Data is 0x800-aligned in the QPK.
  QPK  header 0x800 bytes: 'QPK\\0', u32 count, same timestamp, zero padding.
  CZL  'CZL\\0', u32 compressed_len, u32 raw_len, then a zlib stream.
  Entry names live in IDX/DATA0.HKT: after the 'PACK_<NAME>_TOP' marker, one
  null-terminated name per entry, starting at entry 1.

Usage:
  qpk.py names  <DATA0.HKT> <names.json>
  qpk.py unpack <DATA_dir> <PACK> <out_dir> [names.json]
  qpk.py pack   <orig_DATA_dir> <PACK> <in_dir> <new_DATA_dir> [names.json]
       Rebuilds PACK.QPK/QPI. For every entry, a replacement file in in_dir
       (same file name unpack produced) is used if present, otherwise the
       original bytes are copied unchanged.
"""
import json, os, re, struct, sys, zlib

ALIGN = 0x800

def read_qpi(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'QPI\0', path
    n = struct.unpack_from('<I', d, 4)[0]
    ts = d[8:16]
    ents = [struct.unpack_from('<II', d, 0x14 + i * 8) for i in range(n)]
    return ts, ents

def load_names(hkt):
    d = open(hkt, 'rb').read()
    packs, cur = {}, None
    for m in re.finditer(rb'([\x21-\x7e]{3,})\x00', d):
        n = m.group(1).decode()
        if n.startswith('PACK_') and n.endswith('_TOP'):
            cur = n[5:-4]; packs[cur] = []
        elif cur:
            packs[cur].append(n)
    return packs

def ext_for(blob):
    m = blob[:4]
    if m[:3] in (b'\x00\x01\x01', b'\x00\x00\x02'): return '.tga'
    for k, e in [(b'\x89PNG', '.png'), (b'HAM\0', '.ham'), (b'HDG\0', '.hdg'),
                 (b'GOF\0', '.gof'), (b'AKB\0', '.akb'), (b'RIFF', '.at9')]:
        if m == k: return e
    return '.bin'

def entry_filename(i, names, blob):
    nm = names[i - 1] if names and 0 < i <= len(names) else None
    if nm:
        nm = re.sub(r'[^\w.\-]', '_', nm)
        return f'{i:04d}_{nm}' + ('' if os.path.splitext(nm)[1] else ext_for(blob))
    return f'{i:04d}' + ext_for(blob)

def read_entry(f, off, sz):
    f.seek(off); hdr = f.read(12)
    if sz & 0x40000000:
        assert hdr[:4] == b'CZL\0'
        cs, raw = struct.unpack_from('<II', hdr, 4)
        blob = zlib.decompressobj().decompress(f.read(cs + 16))
        assert len(blob) == raw == sz & 0x3fffffff
        return blob
    f.seek(off); return f.read(sz & 0x3fffffff)

def unpack(data_dir, pack, out, names=None):
    os.makedirs(out, exist_ok=True)
    ts, ents = read_qpi(os.path.join(data_dir, pack + '.QPI'))
    nl = names.get(pack) if names else None
    with open(os.path.join(data_dir, pack + '.QPK'), 'rb') as f:
        for i, (off, sz) in enumerate(ents):
            if sz & 0x80000000: continue
            blob = read_entry(f, off, sz)
            open(os.path.join(out, entry_filename(i, nl, blob)), 'wb').write(blob)

def czl(blob):
    c = zlib.compress(blob, 9)
    return b'CZL\0' + struct.pack('<II', len(c), len(blob)) + c

def pack(orig_dir, pk, in_dir, new_dir, names=None, repl_bytes=None):
    """in_dir: folder of NNNN_* replacement files, or None. repl_bytes: {index: bytes}."""
    os.makedirs(new_dir, exist_ok=True)
    ts, ents = read_qpi(os.path.join(orig_dir, pk + '.QPI'))
    repl = dict(repl_bytes or {})
    if in_dir and os.path.isdir(in_dir):
        for fn in os.listdir(in_dir):
            m = re.match(r'(\d{4})', fn)
            if m: repl[int(m.group(1))] = os.path.join(in_dir, fn)
    out_ents = []
    with open(os.path.join(orig_dir, pk + '.QPK'), 'rb') as f, \
         open(os.path.join(new_dir, pk + '.QPK'), 'wb') as o:
        o.write((b'QPK\0' + struct.pack('<I', len(ents)) + ts).ljust(ALIGN, b'\0'))
        changed = 0
        cursor = 0x14            # empty slots record the unaligned end of the previous file
        live = [i for i, (_, s_) in enumerate(ents) if not s_ & 0x80000000]
        last = live[-1] if live else -1
        for i, (off, sz) in enumerate(ents):
            if sz & 0x80000000:
                out_ents.append((cursor, 0x80000000)); continue
            if i in repl:
                blob = repl[i] if isinstance(repl[i], bytes) else open(repl[i], 'rb').read(); changed += 1
                stored = czl(blob) if sz & 0x40000000 else blob
                raw = len(blob)
            else:
                # copy original stored bytes verbatim (no recompression)
                f.seek(off)
                if sz & 0x40000000:
                    cs = struct.unpack_from('<I', f.read(8), 4)[0]
                    f.seek(off); stored = f.read(12 + cs)
                else:
                    stored = f.read(sz & 0x3fffffff)
                raw = sz & 0x3fffffff
            al = ALIGN if off % ALIGN == 0 else 4   # a few dummy files are only 4-aligned
            o.write(b'\0' * (-o.tell() % al))
            pos = o.tell()
            o.write(stored)
            cursor = o.tell()
            out_ents.append((pos, raw | (sz & 0x40000000)))
    q = b'QPI\0' + struct.pack('<I', len(ents)) + ts + b'\0' * 4
    q += b''.join(struct.pack('<II', p, s) for p, s in out_ents) + struct.pack('<II', cursor, 0)
    open(os.path.join(new_dir, pk + '.QPI'), 'wb').write(q)
    print(f'{pk}: {len(ents)} entries, {changed} replaced')

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if a[0] == 'names':
        json.dump(load_names(a[1]), open(a[2], 'w'), indent=0)
    elif a[0] == 'unpack':
        unpack(a[1], a[2], a[3], json.load(open(a[4])) if len(a) > 4 else None)
    elif a[0] == 'pack':
        pack(a[1], a[2], a[3], a[4], json.load(open(a[5])) if len(a) > 5 else None)
    else:
        sys.exit(__doc__)
