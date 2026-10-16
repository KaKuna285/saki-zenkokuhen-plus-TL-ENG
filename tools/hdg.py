#!/usr/bin/env python3
"""HDG container (HOTDOG.QPK entries: animated screens with their own texture copies).
  'HDG\\0', u32 count, u32 name_table_offset
  count * (u32 offset, u32 raw_size|flags, u32 name_offset, u32 0, u32 0)
  data (16-aligned, CZL-compressed when flag 0x40000000), then the name table."""
import struct, zlib

def parse(d):
    n, ntab = struct.unpack_from('<II', d, 4)
    ents = [list(struct.unpack_from('<IIIII', d, 0xc + i * 20)) for i in range(n)]
    return n, ntab, ents

def stored_len(d, off, sz):
    if sz & 0x40000000:
        return 12 + struct.unpack_from('<I', d, off + 4)[0]
    return sz & 0x3fffffff

def member(d, off, sz):
    if sz & 0x40000000:
        cs, raw = struct.unpack_from('<II', d, off + 4)
        return zlib.decompressobj().decompress(d[off + 12:off + 12 + cs + 16])
    return d[off:off + (sz & 0x3fffffff)]

def members(d):
    n, ntab, ents = parse(d)
    for i, (off, sz, *_r) in enumerate(ents):
        yield i, member(d, off, sz)

def rebuild(d, replace):
    """replace: {index: new raw bytes}. Returns new HDG bytes (identical if replace is empty)."""
    n, ntab, ents = parse(d)
    if n == 0: return d
    first = ents[0][0]
    out = bytearray(d[:first])          # header + table + original padding
    for i, e in enumerate(ents):
        off, sz = e[0], e[1]
        if i in replace:
            raw = replace[i]
            if sz & 0x40000000:
                c = zlib.compress(raw, 9)
                st = b'CZL\0' + struct.pack('<II', len(c), len(raw)) + c
            else:
                st = raw
            e[1] = len(raw) | (sz & 0x40000000)
        else:
            st = d[off:off + stored_len(d, off, sz)]
        out += b'\0' * (-len(out) % 16)
        e[0] = len(out)
        out += st
    last_off, last_sz = parse(d)[2][-1][:2]
    tail_gap = ntab - (last_off + stored_len(d, last_off, last_sz))   # padding before name table
    out += b'\0' * tail_gap if tail_gap >= 0 else b''
    new_ntab = len(out)
    out += d[ntab:]
    struct.pack_into('<I', out, 8, new_ntab)
    for i, e in enumerate(ents):
        struct.pack_into('<IIIII', out, 0xc + i * 20, *e)
    return bytes(out)

def names(d):
    """Member names from the HDG name table (list, same order as members)."""
    n, ntab, ents = parse(d)
    out = []
    for e in ents:
        p = ntab + e[2]
        out.append(d[p:d.index(b'\0', p)].decode('ascii', 'replace'))
    return out
