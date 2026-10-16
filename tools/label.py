#!/usr/bin/env python3
"""Make English button labels in the game's menu style.

EASY MODE - give a button name (without _on/_off/_hold) and the English text:

    python3 tools/label.py s3_mmenu_btn_txt_team "Team"

  -> finds every state of that button in work/ja/ (…_on, …_off, …_hold, …_disable),
     draws "Team" in the matching style for each state, and saves them into
     work/en/ (same sub-folder and file name as the original).

Several buttons in one go:

    python3 tools/label.py s3_mmenu_btn_txt_team "Team" s3_mmenu_btn_txt_solo "Solo"

Options (put them before the names):
    --size N         starting font size (default 26, or fitted to the plate with --charname;
                     shrinks automatically if the text is too wide)
    --font PATH      a .ttf/.otf font file (default: DejaVu Sans Bold; DejaVu Sans with --charname)
    --preview        also writes work/preview_<name>.png showing original vs English
    --charname       character-name plate style (white->green text, black outline,
                     thick orange bevelled border), e.g.
                     python3 tools/label.py --charname s3_chr01_tak_name "Yuuki Kataoka"

Styles (picked automatically from the file name):
    _on       black text, white outline, orange glow        (cursor on the button)
    _off      white text, grey outline                      (not selected)
    _hold     white->yellow text, dark outline              (being pressed)
    _disable  grey text, dark outline                       (can't be selected)
"""
import collections, glob, os, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = ['/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
         '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf']
CHARNAME_FONTS = ['/usr/share/fonts/TTF/DejaVuSans.ttf',
                  '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                  '/usr/share/fonts/dejavu/DejaVuSans.ttf']

# fill (top, bottom), outline, glow colour, glow radius
STYLES = {
    'on':      ((0, 0, 0), (0, 0, 0), (255, 255, 255), (255, 119, 1), 3),
    'off':     ((255, 255, 255), (255, 255, 255), (75, 77, 74), (40, 40, 40), 2),
    'hold':    ((255, 252, 240), (253, 210, 64), (21, 21, 21), (21, 21, 21), 2),
    'disable': ((150, 150, 150), (150, 150, 150), (50, 50, 50), (30, 30, 30), 2),
}

def style_for(name):
    for k in STYLES:
        if name.endswith('_' + k): return STYLES[k]
    return STYLES['off']

def sample_glow(im):
    px = im.convert('RGBA')
    px = px.get_flattened_data() if hasattr(px, 'get_flattened_data') else px.getdata()
    c = collections.Counter(p[:3] for p in px if 20 < p[3] < 200)
    return c.most_common(1)[0][0] if c else None

def render(size_wh, text, style, font_path, size=26, stroke_w=2):
    W, H = size_wh
    top, bottom, stroke, glow, gr = style
    f = ImageFont.truetype(font_path, size)
    while True:   # shrink until it fits
        l, t, r, b = ImageDraw.Draw(Image.new('L', (1, 1))).textbbox((0, 0), text, font=f, stroke_width=stroke_w)
        if (r - l <= W - 2 * (gr + 4) and b - t <= H - 4) or f.size <= 10: break
        f = ImageFont.truetype(font_path, f.size - 1)
    x, y = (W - (r - l)) // 2 - l, (H - (b - t)) // 2 - t
    # glow
    m = Image.new('L', (W, H)); ImageDraw.Draw(m).text((x, y), text, font=f, fill=255, stroke_width=stroke_w + 1)
    out = Image.new('RGBA', (W, H), glow + (0,)); out.putalpha(m.filter(ImageFilter.GaussianBlur(gr)))
    # outline
    so = Image.new('L', (W, H)); ImageDraw.Draw(so).text((x, y), text, font=f, fill=255, stroke_width=stroke_w)
    out.alpha_composite(Image.composite(Image.new('RGBA', (W, H), stroke + (255,)), Image.new('RGBA', (W, H)), so))
    # fill, with a vertical gradient between top and bottom colour
    fm = Image.new('L', (W, H)); ImageDraw.Draw(fm).text((x, y), text, font=f, fill=255)
    grad = Image.new('RGBA', (W, H))
    y0, y1 = y + t, y + b
    for yy in range(H):
        k = min(1, max(0, (yy - y0) / max(1, y1 - y0)))
        c = tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3))
        ImageDraw.Draw(grad).line([(0, yy), (W, yy)], fill=c + (255,))
    out.alpha_composite(Image.composite(grad, Image.new('RGBA', (W, H)), fm))
    return out

def _dilate(m, r):
    """Roughly round dilation of an L mask by r pixels (alternating cross / square steps)."""
    for i in range(r):
        if i % 2 == 0:
            out = m.copy()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                out = ImageChops.lighter(out, ImageChops.offset(m, dx, dy))
            m = out
        else:
            m = m.filter(ImageFilter.MaxFilter(3))
    return m

# character-name plate: (distance from the letters in px, colour, alpha), drawn outside-in
CHARNAME_RING = [(6, (34, 21, 1), 150), (5, (118, 73, 1), 255), (4, (208, 130, 1), 255),
                 (3, (109, 68, 1), 255), (2, (0, 0, 0), 255)]
CHARNAME_FILL = [(0.0, (250, 255, 252)), (0.45, (185, 240, 200)), (1.0, (70, 225, 110))]

def render_charname(size_wh, text, font_path, size=None):
    W, H = size_wh
    pad = CHARNAME_RING[0][0]
    f = ImageFont.truetype(font_path, size or max(10, H - 10))
    while True:
        l, t, r, b = ImageDraw.Draw(Image.new('L', (1, 1))).textbbox((0, 0), text, font=f)
        if (r - l <= W - 2 * pad and b - t <= H - 2 * pad) or f.size <= 8: break
        f = ImageFont.truetype(font_path, f.size - 1)
    x, y = (W - (r - l)) // 2 - l, (H - (b - t)) // 2 - t
    F = Image.new('L', (W, H)); ImageDraw.Draw(F).text((x, y), text, font=f, fill=255)
    out = Image.new('RGBA', (W, H))
    for dist, col, alpha in CHARNAME_RING:
        m = _dilate(F, dist)
        if alpha < 255: m = m.point(lambda v, a=alpha: v * a // 255)
        out.alpha_composite(Image.composite(Image.new('RGBA', (W, H), col + (255,)), Image.new('RGBA', (W, H)), m))
    grad = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(grad)
    y0, y1 = y + t, y + b
    for yy in range(H):
        k = min(1, max(0, (yy - y0) / max(1, y1 - y0)))
        for (k0, c0), (k1, c1) in zip(CHARNAME_FILL, CHARNAME_FILL[1:]):
            if k0 <= k <= k1:
                u = (k - k0) / (k1 - k0); c = tuple(int(c0[i] + (c1[i] - c0[i]) * u) for i in range(3)); break
        d.line([(0, yy), (W, yy)], fill=c + (255,))
    out.alpha_composite(Image.composite(grad, Image.new('RGBA', (W, H)), F))
    return out

def find_states(base):
    hits = [p for p in glob.glob(os.path.join(ROOT, 'work', 'ja', '**', '*.png'), recursive=True)
            if os.path.basename(p)[:-4] == base or
            (os.path.basename(p).startswith(base + '_') and os.path.basename(p)[len(base) + 1:-4] in STYLES)]
    return sorted(hits)

def main(argv):
    size, font, preview, charname, args = None, None, False, False, []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--size': size = int(argv[i + 1]); i += 2
        elif a == '--font': font = argv[i + 1]; i += 2
        elif a == '--preview': preview = True; i += 1
        elif a == '--charname': charname = True; i += 1
        elif a in ('-h', '--help'): sys.exit(__doc__)
        else: args.append(a); i += 1
    if not args or len(args) % 2: sys.exit(__doc__)
    font = font or next((p for p in (CHARNAME_FONTS if charname else []) + FONTS if os.path.exists(p)), None)
    if not font: sys.exit('No font found - pass one with --font /path/to/font.ttf')
    for base, text in zip(args[::2], args[1::2]):
        base = os.path.basename(base)
        if base.endswith('.png'): base = base[:-4]
        files = find_states(base)
        if not files:
            print(f'!! nothing in work/ja matches "{base}" - check the name'); continue
        pv = []
        for src in files:
            name = os.path.basename(src)[:-4]
            orig = Image.open(src).convert('RGBA')
            if charname:
                img = render_charname(orig.size, text, font, size)
            else:
                st = list(style_for(name))
                if name.endswith('_on'):
                    st[3] = sample_glow(orig) or st[3]       # keep the original glow colour
                img = render(orig.size, text, tuple(st), font, size or 26)
            dst = os.path.join(ROOT, 'work', 'en', os.path.relpath(src, os.path.join(ROOT, 'work', 'ja')))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            img.save(dst); pv.append((orig, img))
            print(f'   wrote work/en/{os.path.relpath(dst, os.path.join(ROOT, "work", "en"))}')
        if preview:
            W, H = pv[0][0].size
            sheet = Image.new('RGBA', (W * 2, H * len(pv)), (70, 90, 130, 255))
            for k, (o, e) in enumerate(pv):
                sheet.alpha_composite(o.resize((W, H)), (0, k * H)); sheet.alpha_composite(e.resize((W, H)), (W, k * H))
            p = os.path.join(ROOT, 'work', f'preview_{base}.png'); sheet.save(p); print(f'   preview: work/preview_{base}.png')

if __name__ == '__main__':
    main(sys.argv[1:])
