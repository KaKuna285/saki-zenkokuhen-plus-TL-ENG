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
    --font PATH      a .ttf/.otf font file (default: DejaVu Sans Bold; DejaVu Sans with --charname;
                     DejaVu Sans Condensed with --help_btn / --yaku)
    --preview        also writes work/preview_<name>.png showing original vs English
    --charname       character-name plate style (white->green text, black outline,
                     thick orange bevelled border), e.g.
                     python3 tools/label.py --charname s3_chr01_tak_name "Yuuki Kataoka"
    --help_btn       help-bar button style (white text, dark border, cream rim, brown shadow,
                     left-aligned; greyed-out originals stay grey), e.g.
                     python3 tools/label.py --help_btn s3_com_help_btn_txt_01 "Confirm"
                     Two centred lines: put \\n in the text, e.g. "Bonus\\nChallenge"
    --yaku           result-screen yaku line (light-blue text, blue rim, navy shadow): the
                     name on the left, a gap for the han number the game draws, then "Han", e.g.
                     python3 tools/label.py --yaku s3_rst_yaku02 "Riichi"
    --title          mode-title style (white->gold text, brown edge, cream rim, shadow,
                     left-aligned). Anything from the first ~ is drawn smaller, e.g.
                     python3 tools/label.py --title s3_com_mode_title_txt03 "Free Match ~Singles~"

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

# help-bar buttons (s3_com_help_btn_txt_*): white text, black edge, dark band, cream rim,
# soft brown drop shadow; left-aligned. Greyed-out originals get the grey palette.
HELPBTN = {'fill': (255, 255, 255), 'edge': (0, 0, 0), 'band': (59, 56, 51), 'rim': (245, 236, 208)}
HELPBTN_GREY = {'fill': (0, 0, 0), 'edge': (81, 81, 81), 'band': (112, 112, 112), 'rim': (215, 215, 215)}
HELPBTN_SHADOW = ((107, 81, 46), 191, (2, 3))
CONDENSED_FONTS = ['/usr/share/fonts/TTF/DejaVuSansCondensed.ttf',
                   '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf',
                   '/usr/share/fonts/dejavu/DejaVuSansCondensed.ttf']

def is_grey_original(orig):
    px = orig.get_flattened_data() if hasattr(orig, 'get_flattened_data') else orig.getdata()
    return sum(1 for p in px if p[3] > 250 and p[0] > 250 and p[1] > 250 and p[2] > 250) < 20

def render_helpbtn(size_wh, text, font_path, size=None, grey=False):
    W, H = size_wh
    pal = HELPBTN_GREY if grey else HELPBTN
    left, right = 5, 5
    text = text.replace('\\n', '\n')           # "Bonus\nChallenge" -> two centred lines
    multi = '\n' in text
    f = ImageFont.truetype(font_path, size or (14 if multi else 20))
    probe = ImageDraw.Draw(Image.new('L', (1, 1)))
    while True:
        l, t, r, b = probe.multiline_textbbox((0, 0), text, font=f, align='center', spacing=0)
        if (r - l <= W - left - right and b - t <= H - (8 if multi else 16)) or f.size <= 8: break
        f = ImageFont.truetype(font_path, f.size - 1)
    x = (W - (r - l)) // 2 - l if multi else left - l
    y = (H - (b - t)) // 2 - t
    F = Image.new('L', (W, H)); ImageDraw.Draw(F).multiline_text((x, y), text, font=f, fill=255, align='center', spacing=0)
    clear = Image.new('RGBA', (W, H))
    def layer(mask, col, alpha=255):
        if alpha < 255: mask = mask.point(lambda v: v * alpha // 255)
        return Image.composite(Image.new('RGBA', (W, H), col + (255,)), clear, mask)
    rim_soft = _dilate(F, 4).filter(ImageFilter.GaussianBlur(0.5))
    rim = _dilate(F, 3)
    col, alpha, (dx, dy) = HELPBTN_SHADOW
    sh = Image.new('L', (W, H)); sh.paste(rim_soft, (dx, dy))          # shift without wrap-around
    out = layer(sh.filter(ImageFilter.GaussianBlur(1)), col, alpha)
    out.alpha_composite(layer(rim_soft, pal['rim'], 200))
    out.alpha_composite(layer(rim, pal['rim']))
    out.alpha_composite(layer(_dilate(F, 2), pal['band']))
    out.alpha_composite(layer(_dilate(F, 1), pal['edge']))
    out.alpha_composite(layer(F, pal['fill']))
    return out

# mode titles (s3_com_mode_title_txt*): white->gold text, dark-brown edge, brown/tan bands,
# cream rim, brown drop shadow; left-aligned. "Main ~sub~" draws the ~sub~ part smaller.
TITLE_RINGS = [(4, (251, 235, 174)), (3, (168, 148, 107)), (2, (83, 60, 38)), (1, (37, 16, 1))]
TITLE_FILL = [(0.0, (255, 255, 255)), (0.45, (253, 244, 205)), (1.0, (250, 222, 125))]
TITLE_SHADOW = ((105, 80, 46), 190, (2, 4))
BOLD_FONTS = FONTS

def _grad_img(W, H, y0, y1, stops):
    g = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(g)
    for yy in range(H):
        k = min(1, max(0, (yy - y0) / max(1, y1 - y0)))
        for (k0, c0), (k1, c1) in zip(stops, stops[1:]):
            if k0 <= k <= k1:
                u = (k - k0) / (k1 - k0); c = tuple(int(c0[i] + (c1[i] - c0[i]) * u) for i in range(3)); break
        d.line([(0, yy), (W, yy)], fill=c + (255,))
    return g

def render_title(size_wh, text, font_path, size=None):
    W, H = size_wh
    left, right = 20, 8
    i = text.find('~')
    main, sub = (text[:i].rstrip(), text[i:].strip()) if i > 0 else (text.strip(), '')
    fs = size or 24
    probe = ImageDraw.Draw(Image.new('L', (1, 1)))
    while True:
        fm = ImageFont.truetype(font_path, fs); fsub = ImageFont.truetype(font_path, max(8, round(fs * 0.72)))
        wm = probe.textlength(main, font=fm); gap = fs * 0.6 if sub else 0
        ws = probe.textlength(sub, font=fsub) if sub else 0
        asc = fm.getbbox('Ag', anchor='ls'); hh = asc[3] - asc[1]
        if (wm + gap + ws <= W - left - right and hh <= H - 12) or fs <= 8: break
        fs -= 1
    # vertical: centre the main line's cap-height-to-descender box a bit above the middle (room for shadow)
    top, bot = fm.getbbox('A', anchor='ls')[1], fm.getbbox('g', anchor='ls')[3]
    base = round((H - 4) / 2 - (top + bot) / 2)
    F = Image.new('L', (W, H)); d = ImageDraw.Draw(F)
    d.text((left, base), main, font=fm, fill=255, anchor='ls')
    if sub: d.text((left + wm + gap, base), sub, font=fsub, fill=255, anchor='ls')
    clear = Image.new('RGBA', (W, H))
    def layer(mask, col, alpha=255):
        if alpha < 255: mask = mask.point(lambda v: v * alpha // 255)
        return Image.composite(Image.new('RGBA', (W, H), col + (255,)), clear, mask)
    outer = _dilate(F, TITLE_RINGS[0][0]).filter(ImageFilter.GaussianBlur(0.5))
    col, alpha, (dx, dy) = TITLE_SHADOW
    sh = Image.new('L', (W, H)); sh.paste(outer, (dx, dy))
    out = layer(sh.filter(ImageFilter.GaussianBlur(1)), col, alpha)
    out.alpha_composite(layer(outer, TITLE_RINGS[0][1]))
    for dist, c in TITLE_RINGS[1:]:
        out.alpha_composite(layer(_dilate(F, dist), c))
    out.alpha_composite(Image.composite(_grad_img(W, H, base + top, base, TITLE_FILL), clear, F))
    return out

# yaku lines on the result screen (s3_rst_yaku01-28, 280x40): name on the left (x 33-182),
# a gap where the game draws the han number itself (x ~190-222), then "Han" (x ~224-256).
YAKU_FILL = [(0.0, (225, 238, 250)), (1.0, (192, 244, 253))]
YAKU_RIM = (22, 55, 152)
YAKU_SHADOW = ((0, 16, 64), 205, (2, 3))
YAKU_NAME_BOX = (33, 182)
YAKU_HAN_BOX = (223, 257)

def render_yaku(size_wh, text, font_path, size=None, han='Han'):
    W, H = size_wh
    probe = ImageDraw.Draw(Image.new('L', (1, 1)))
    def fit(t, box_w, start):
        f = ImageFont.truetype(font_path, start)
        while probe.textlength(t, font=f) > box_w and f.size > 8:
            f = ImageFont.truetype(font_path, f.size - 1)
        return f
    fn = fit(text, YAKU_NAME_BOX[1] - YAKU_NAME_BOX[0], size or 22)
    fh = fit(han, YAKU_HAN_BOX[1] - YAKU_HAN_BOX[0], 20) if han else None
    top, bot = fn.getbbox('H', anchor='ls')[1], 0
    base = round(21.5 - top / 2)                         # capital letters centred where the kanji sit
    F = Image.new('L', (W, H)); d = ImageDraw.Draw(F)
    d.text((YAKU_NAME_BOX[0], base), text, font=fn, fill=255, anchor='ls')
    if han:
        hw = probe.textlength(han, font=fh)
        d.text((YAKU_HAN_BOX[0] + (YAKU_HAN_BOX[1] - YAKU_HAN_BOX[0] - hw) / 2, base), han, font=fh, fill=255, anchor='ls')
    # make the white letters a little thicker: add a soft half-pixel around each stroke
    F = ImageChops.lighter(F, _dilate(F, 1).point(lambda v: v * 225 // 255))
    clear = Image.new('RGBA', (W, H))
    def layer(mask, col, alpha=255):
        if alpha < 255: mask = mask.point(lambda v: v * alpha // 255)
        return Image.composite(Image.new('RGBA', (W, H), col + (255,)), clear, mask)
    rim = _dilate(F, 3); rim_soft = _dilate(F, 4).filter(ImageFilter.GaussianBlur(0.6))
    col, alpha, (dx, dy) = YAKU_SHADOW
    sh = Image.new('L', (W, H)); sh.paste(rim_soft, (dx, dy))
    out = layer(sh, col, alpha)
    out.alpha_composite(layer(rim_soft, YAKU_RIM, 170))
    out.alpha_composite(layer(rim, YAKU_RIM))
    out.alpha_composite(Image.composite(_grad_img(W, H, base + top, base, YAKU_FILL), clear, F))
    return out

def find_states(base):
    hits = [p for p in glob.glob(os.path.join(ROOT, 'work', 'ja', '**', '*.png'), recursive=True)
            if os.path.basename(p)[:-4] == base or
            (os.path.basename(p).startswith(base + '_') and os.path.basename(p)[len(base) + 1:-4] in STYLES)]
    return sorted(hits)

def main(argv):
    size, font, preview, charname, helpbtn, title, yaku, args = None, None, False, False, False, False, False, []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--size': size = int(argv[i + 1]); i += 2
        elif a == '--font': font = argv[i + 1]; i += 2
        elif a == '--preview': preview = True; i += 1
        elif a == '--charname': charname = True; i += 1
        elif a in ('--help_btn', '--help-btn'): helpbtn = True; i += 1
        elif a == '--title': title = True; i += 1
        elif a == '--yaku': yaku = True; i += 1
        elif a in ('-h', '--help'): sys.exit(__doc__)
        else: args.append(a); i += 1
    if not args or len(args) % 2: sys.exit(__doc__)
    font = font or next((p for p in (CHARNAME_FONTS if charname else []) + (CONDENSED_FONTS if (helpbtn or yaku) else []) + FONTS if os.path.exists(p)), None)
    if not font: sys.exit('No font found - pass one with --font /path/to/font.ttf')
    for base, text in zip(args[::2], args[1::2]):
        # Japanese wave dashes aren't in the Latin fonts (they'd draw as a box) -> plain ~
        text = text.replace('\u301c', '~').replace('\uff5e', '~')
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
            elif yaku:
                img = render_yaku(orig.size, text, font, size)
            elif title:
                img = render_title(orig.size, text, font, size)
            elif helpbtn:
                img = render_helpbtn(orig.size, text, font, size, grey=is_grey_original(orig))
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
