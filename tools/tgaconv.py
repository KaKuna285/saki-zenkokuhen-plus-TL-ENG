#!/usr/bin/env python3
"""Convert this game's TGA textures to/from PNG.

  tgaconv.py export <dir_with_tga> <png_out_dir> [glob]
  tgaconv.py import <png_dir> <orig_tga_dir> <tga_out_dir>
      For each edited PNG, writes a TGA in the same format as the original
      (8-bit paletted w/ 32-bit BGRA palette, or 32-bit BGRA truecolor),
      bottom-up row order like the originals. Size must match the original
      unless you know the layout (HAM) tolerates it - a warning is printed.
"""
import fnmatch, os, struct, sys
from PIL import Image

def load(d):
    """Returns (RGBA image, fmt) where fmt=(type, palette_bits, bpp, desc)."""
    idl, cmt, typ, cmfirst, cmlen, cmbits, _, _, w, h, bpp, desc = struct.unpack_from('<BBBHHBHHHHBB', d, 0)
    p = 18 + idl
    if typ == 1 and bpp == 8 and cmbits in (24, 32):
        e = cmbits // 8
        pal = d[p:p + cmlen * e]; p += len(pal)
        im = Image.frombytes('P', (w, h), d[p:p + w * h])
        rgba = b''.join(bytes((pal[i*e+2], pal[i*e+1], pal[i*e], pal[i*e+3] if e == 4 else 255)) for i in range(cmlen))
        im.putpalette(rgba, rawmode='RGBA'); im = im.convert('RGBA')
    elif typ == 2 and bpp in (24, 32):
        mode = 'BGRA' if bpp == 32 else 'BGR'
        im = Image.frombytes('RGBA' if bpp == 32 else 'RGB', (w, h), d[p:p + w * h * bpp // 8], 'raw', mode).convert('RGBA')
    else:
        raise ValueError(f'unsupported TGA type {typ}/{bpp}bpp/{cmbits}')
    if not desc & 0x20:
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    return im, (typ, cmbits, bpp, desc)

def save(im, fmt):
    typ, cmbits, bpp, desc = fmt
    im = im.convert('RGBA'); w, h = im.size
    if not desc & 0x20:
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    if typ == 2:
        hdr = struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, w, h, bpp, desc)
        return hdr + im.tobytes('raw', 'BGRA' if bpp == 32 else 'BGR')
    if cmbits == 32:
        q = im.quantize(256, method=Image.Quantize.FASTOCTREE)
    else:
        q = im.convert('RGB').quantize(256)
    pal = bytes(q.getpalette(rawmode='RGBA'))[:1024].ljust(1024, b'\0')
    e = cmbits // 8
    cm = b''.join(bytes((pal[i*4+2], pal[i*4+1], pal[i*4]) + ((pal[i*4+3],) if e == 4 else ())) for i in range(256))
    hdr = struct.pack('<BBBHHBHHHHBB', 0, 1, 1, 0, 256, cmbits, 0, 0, w, h, 8, desc)
    return hdr + cm + q.tobytes()

def export(src, out, pat='*'):
    os.makedirs(out, exist_ok=True); n = 0
    for fn in sorted(os.listdir(src)):
        if not fn.endswith('.tga') or not fnmatch.fnmatch(fn, pat): continue
        im, _ = load(open(os.path.join(src, fn), 'rb').read())
        im.save(os.path.join(out, fn[:-4] + '.png')); n += 1
    print(f'exported {n}')

def import_(pngs, orig, out):
    os.makedirs(out, exist_ok=True); n = 0
    for fn in sorted(os.listdir(pngs)):
        if not fn.endswith('.png'): continue
        base = fn[:-4] + '.tga'
        oim, fmt = load(open(os.path.join(orig, base), 'rb').read())
        im = Image.open(os.path.join(pngs, fn))
        if im.size != oim.size:
            print(f'WARNING {fn}: size {im.size} != original {oim.size}')
        open(os.path.join(out, base), 'wb').write(save(im, fmt)); n += 1
    print(f'imported {n}')

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['export']: export(a[1], a[2], a[3] if len(a) > 3 else '*')
    elif a[:1] == ['import']: import_(a[1], a[2], a[3])
    else: sys.exit(__doc__)
