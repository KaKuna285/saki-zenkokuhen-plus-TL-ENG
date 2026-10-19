#!/usr/bin/env python3
"""Make English button labels in the game's menu style.

EASY MODE - give a button name (without _on/_off/_hold) and the English text:

    python3 tools/label.py s3_mmenu_btn_txt_team "Team"

  -> finds every state of that button in work/ja/ (…_on, …_off, …_hold, …_disable, …_invalid),
     draws "Team" in the matching style for each state, and saves them into
     work/en/ (same sub-folder and file name as the original).

Two lines: put \\n in the text, e.g. "Free\\nMatch".

Several buttons in one go:

    python3 tools/label.py s3_mmenu_btn_txt_team "Team" s3_mmenu_btn_txt_solo "Solo"

Options (put them before the names):
    --size N         starting font size (default 26, or fitted to the plate with --charname;
                     shrinks automatically if the text is too wide)
    --font PATH      a .ttf/.otf font file (default: DejaVu Sans Bold; DejaVu Sans Condensed Bold with --charname;
                     DejaVu Sans Condensed with --help_btn;
                     DejaVu Sans Condensed Bold with --yaku / --rule / --cmd)
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
    --yakuman        yakuman banner on the result screen (big shiny gold letters with bevel
                     lighting, dark edge, white rim, heavy shadow, centred). Long names: squeezed, or use \\n for two lines, e.g.
                     python3 tools/label.py --yakuman s3_rst_yaku32 "Tenhou"
    --rule           rules-screen style: picks the right look per state for s3_rule_txt* (on = orange-red,
                     off = grey, hold = white) and s3_rule_item_txt_* (on = orange glow, hold = yellow), e.g.
                     python3 tools/label.py --rule s3_rule_txt01 "1 Game"
    --chg_info       in-match challenge info (s3_tak_chg_info_*): "~ Clear Condition ~" on top and
                     your text underneath, both centred, white with grey outline and dark glow, e.g.
                     python3 tools/label.py --chg_info s3_tak_chg_info_02 "Win a hand"
                     (own header: "Header\\nCondition")
    --cmd            in-match command labels (s3_tak_cmd_NN): makes both _1 (white, grey outline)
                     and _2 (cream, brown outline), e.g.
                     python3 tools/label.py --cmd s3_tak_cmd_01 "Pon"
    --title          mode-title style (white->gold text, brown edge, cream rim, shadow,
                     left-aligned). Anything from the first ~ is drawn smaller, e.g.
                     python3 tools/label.py --title s3_com_mode_title_txt03 "Free Match ~Singles~"

Styles (picked automatically from the file name):
    _on       black text, white outline, orange glow        (cursor on the button)
    _off      white text, grey outline                      (not selected)
    _hold     white->yellow text, dark outline              (being pressed)
    _disable  grey text, dark outline                       (can't be selected)
    _invalid  grey text, black outline                      (can't be used, e.g. training stats)
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
    'invalid': ((144, 144, 144), (131, 131, 131), (0, 0, 0), (0, 0, 0), 2),
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

def render(size_wh, text, style, font_path, size=26, stroke_w=2, margin=14):
    W, H = size_wh
    top, bottom, stroke, glow, gr = style
    lines = text.replace('\\n', '\n').split('\n')   # "Free\nMatch" -> two centred lines
    probe = ImageDraw.Draw(Image.new('L', (1, 1)))
    f = ImageFont.truetype(font_path, size)
    while True:   # shrink until it fits
        gap = 6 if len(lines) > 1 else 0
        lh = -f.getbbox('H', anchor='ls')[1] + gap            # capital height + gap per line
        boxes = [probe.textbbox((0, 0), ln, font=f, stroke_width=stroke_w, anchor='ls') for ln in lines]
        wmax = max(bx[2] - bx[0] for bx in boxes)
        t, b = boxes[0][1], (len(lines) - 1) * lh + boxes[-1][3]
        if (wmax <= W - margin and b - t <= H - 4) or f.size <= 10: break   # same margin for every state
        f = ImageFont.truetype(font_path, f.size - 1)
    y = (H - (b - t)) // 2 - t
    pos = [((W - (bx[2] - bx[0])) // 2 - bx[0], y + k * lh) for k, bx in enumerate(boxes)]
    def mask(stroke):
        m = Image.new('L', (W, H)); d = ImageDraw.Draw(m)
        for (px, py), ln in zip(pos, lines): d.text((px, py), ln, font=f, fill=255, stroke_width=stroke, anchor='ls')
        return m
    # glow
    out = Image.new('RGBA', (W, H), glow + (0,)); out.putalpha(mask(stroke_w + 1).filter(ImageFilter.GaussianBlur(gr)))
    # outline
    out.alpha_composite(Image.composite(Image.new('RGBA', (W, H), stroke + (255,)), Image.new('RGBA', (W, H)), mask(stroke_w)))
    # fill, with a vertical gradient between top and bottom colour (one gradient over all lines)
    fm = mask(0)
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
CHARNAME_FILL = [  # matched to the green score digits (s3_tak_scr_green_*): saturated green,
    (0.00, (40, 214, 94)), (0.12, (62, 240, 118)), (0.30, (78, 232, 118)),   # narrow white
    (0.42, (165, 240, 186)), (0.48, (242, 253, 246)), (0.54, (168, 226, 150)), # highlight in the
    (0.66, (92, 190, 68)), (0.82, (56, 168, 34)), (1.00, (37, 147, 14))]      # middle, deep green

CHARNAME_RING_SMALL = [(5, (34, 21, 1), 140), (4, (118, 73, 1), 255), (3, (208, 130, 1), 255),
                       (2, (90, 56, 1), 255), (1, (0, 0, 0), 255)]

CHARNAME_REFERENCE = 'Hatsumi Usuzumi'      # a long name: every name uses the size that fits this one
CHARNAME_TALL = 1.2                         # letters this much taller than the font normally is (same width)

def render_charname(size_wh, text, font_path, size=None):
    W, H = size_wh
    pad = CHARNAME_RING[0][0]
    probe = ImageDraw.Draw(Image.new('L', (1, 1)))
    def fits(f, t):
        l, t_, r, b = probe.textbbox((0, 0), t, font=f)
        return r - l <= W - 2 * pad and b - t_ <= H - 2 * pad
    # one uniform size for all names (same letter height and stroke weight); only a name longer
    # than the reference gets smaller
    fs = size or max(10, H - 10)
    if not size:
        while fs > 8 and not fits(ImageFont.truetype(font_path, fs), CHARNAME_REFERENCE): fs -= 1
    while fs > 8 and not fits(ImageFont.truetype(font_path, fs), text): fs -= 1
    # taller letters: draw CHARNAME_TALL times bigger, then narrow them back to the same width.
    # Done at 4x resolution and scaled DOWN, so the result stays sharp (no blur).
    fv = ImageFont.truetype(font_path, max(8, round(fs * CHARNAME_TALL)))
    ref = CHARNAME_REFERENCE if not size else text
    hx = probe.textlength(ref, font=ImageFont.truetype(font_path, fs)) / max(1, probe.textlength(ref, font=fv))
    big = ImageFont.truetype(font_path, fv.size * 4)
    asc, desc = big.getmetrics()
    wb = int(probe.textlength(text, font=big)) + 16
    m = Image.new('L', (wb, asc + desc)); ImageDraw.Draw(m).text((8, asc), text, font=big, fill=255, anchor='ls')
    m = m.resize((max(1, round(wb * hx / 4)), max(1, round((asc + desc) / 4))), Image.LANCZOS)
    cap = -fv.getbbox('H', anchor='ls')[1]
    base = (H + cap) // 2                                   # capitals centred vertically
    bb = m.getbbox() or (0, 0, m.width, m.height)
    F = Image.new('L', (W, H))
    F.paste(m, ((W - (bb[2] - bb[0])) // 2 - bb[0], base - round(asc / 4)))
    out = Image.new('RGBA', (W, H))
    for dist, col, alpha in CHARNAME_RING:
        mm = _dilate(F, dist)
        if alpha < 255: mm = mm.point(lambda v, a=alpha: v * a // 255)
        out.alpha_composite(Image.composite(Image.new('RGBA', (W, H), col + (255,)), Image.new('RGBA', (W, H)), mm))
    # gradient from the top of the capitals to the baseline - identical for every name
    out.alpha_composite(Image.composite(_grad_img(W, H, base - cap, base, CHARNAME_FILL), Image.new('RGBA', (W, H)), F))
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

def _text_mask(text, font, max_w, min_squeeze=0.72):
    """Text as an L mask (cropped to its advance box, baseline at row `asc`). If it is wider
    than max_w it is squeezed horizontally (keeps the letters tall) down to min_squeeze;
    returns (mask, ascent) or None if it still does not fit."""
    asc, desc = font.getmetrics()
    w = int(ImageDraw.Draw(Image.new('L', (1, 1))).textlength(text, font=font)) + 2
    m = Image.new('L', (w, asc + desc)); ImageDraw.Draw(m).text((0, asc), text, font=font, fill=255, anchor='ls')
    if w <= max_w: return m, asc
    if max_w / w < min_squeeze: return None
    return m.resize((max_w, m.height), Image.LANCZOS), asc

def render_yaku(size_wh, text, font_path, size=None, han='Han'):
    W, H = size_wh
    def fit(t, box_w, start, squeeze):
        fs = start
        while True:
            f = ImageFont.truetype(font_path, fs)
            r = _text_mask(t, f, box_w, squeeze)
            if r or fs <= 8: return (r or _text_mask(t, f, box_w, 0.01)), f
            fs -= 1
    (mn, asc), fn = fit(text, YAKU_NAME_BOX[1] - YAKU_NAME_BOX[0], size or 27, 0.72)
    cap = -fn.getbbox('H', anchor='ls')[1]
    base = round(19.5 + cap / 2)                          # capitals centred where the kanji sit (rows 9-29)
    F = Image.new('L', (W, H))
    F.paste(mn, (YAKU_NAME_BOX[0], base - asc))
    if han:
        (mh, asch), fh = fit(han, YAKU_HAN_BOX[1] - YAKU_HAN_BOX[0], 22, 0.8)
        F.paste(mh, (YAKU_HAN_BOX[0] + (YAKU_HAN_BOX[1] - YAKU_HAN_BOX[0] - mh.width) // 2, base - asch))
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
    out.alpha_composite(Image.composite(_grad_img(W, H, base - cap, base, YAKU_FILL), clear, F))
    return out

# yakuman (s3_rst_yaku32-44, 288x80): shiny gold letters (multi-band metallic gradient with a
# soft reflection band + bevel lighting from the top-left), dark-brown edge, white rim and a
# heavy dark drop shadow; centred.
YAKUMAN_FILL = [(0.00, (255, 236, 135)), (0.16, (255, 250, 210)), (0.32, (255, 230, 125)),
                (0.44, (255, 200, 70)), (0.52, (245, 175, 50)), (0.62, (255, 228, 135)),
                (0.70, (255, 246, 185)), (0.80, (255, 218, 95)), (0.90, (252, 192, 62)),
                (1.00, (228, 156, 40))]
YAKUMAN_EDGE = (40, 22, 6)
YAKUMAN_RIM = (255, 255, 255)
YAKUMAN_SHADOW = ((22, 10, 0), 255, (6, 9))

def render_yakuman(size_wh, text, font_path, size=None):
    W, H = size_wh
    lines = text.replace('\\n', '\n').split('\n')
    pad = 12
    fs = size or (64 if len(lines) == 1 else 32)
    while True:
        f = ImageFont.truetype(font_path, fs)
        masks = [_text_mask(l, f, W - 2 * pad, 0.72) for l in lines]
        cap = -f.getbbox('H', anchor='ls')[1]
        lh = cap + (6 if len(lines) > 1 else 0)
        total = lh * len(lines) - (6 if len(lines) > 1 else 0)
        if all(masks) and total <= H - 18 or fs <= 10: break
        fs -= 1
    masks = [m or _text_mask(l, f, W - 2 * pad, 0.01) for m, l in zip(masks, lines)]
    F = Image.new('L', (W, H))
    top = (H - 9 - total) // 2                            # leave room for the drop shadow below
    bases = []
    for k, (m, a) in enumerate(masks):
        base = top + cap + k * lh
        F.paste(m, ((W - m.width) // 2, base - a)); bases.append(base)
    squeezed = any(m.width >= W - 2 * pad for m, _ in masks)
    small = fs < 52 or squeezed
    F = ImageChops.lighter(F, _dilate(F, 1).point(lambda v: v * 200 // 255))   # a bit more gold
    clear = Image.new('RGBA', (W, H))
    def layer(mask, col, alpha=255):
        if alpha < 255: mask = mask.point(lambda v: v * alpha // 255)
        return Image.composite(Image.new('RGBA', (W, H), col + (255,)), clear, mask)
    edge = _dilate(F, 2 if small else 3)
    rim = _dilate(F, 4 if small else 5).filter(ImageFilter.GaussianBlur(0.5))
    col, alpha, (dx, dy) = YAKUMAN_SHADOW
    if small: dx, dy, alpha = 4, 6, 200
    sh = Image.new('L', (W, H)); sh.paste(rim, (dx, dy))
    out = layer(sh, col, alpha)
    out.alpha_composite(layer(rim, YAKUMAN_RIM))
    out.alpha_composite(layer(edge, YAKUMAN_EDGE))
    grad = Image.new('RGBA', (W, H))
    for base in bases:                                     # one gradient per line
        g = _grad_img(W, H, base - cap, base + 2, YAKUMAN_FILL)
        band = Image.new('L', (W, H)); ImageDraw.Draw(band).rectangle([0, base - cap - 10, W, base + 14], fill=255)
        grad = Image.composite(g, grad, band)
    out.alpha_composite(Image.composite(grad, clear, F))
    # bevel lighting: treat the letters as rounded shapes lit from the top-left
    hmap = F.filter(ImageFilter.GaussianBlur(2.2))
    a1 = ImageChops.offset(hmap, 1, 1); a2 = ImageChops.offset(hmap, -1, -1)
    hi = ImageChops.multiply(ImageChops.subtract(a1, a2, scale=0.18), F)   # stronger highlights
    lo = ImageChops.multiply(ImageChops.subtract(a2, a1, scale=0.3), F)
    out.alpha_composite(layer(hi, (255, 246, 190)))
    out.alpha_composite(layer(lo, (140, 85, 15), 100))                        # softer shading
    # glossy sheen: a soft white glaze over the top part of each line
    for base in bases:
        g = Image.new('L', (W, H)); dg = ImageDraw.Draw(g)
        t0 = base - cap - 2; t1 = base - int(cap * 0.45)
        for yy in range(max(0, t0), min(H, t1)):
            dg.line([(0, yy), (W, yy)], fill=int(70 * (1 - (yy - t0) / max(1, t1 - t0))))
        out.alpha_composite(layer(ImageChops.multiply(g, F), (255, 248, 205)))
    return out

# rules screen (mahjong_table/s3_rule_txt*_{on,off,hold} 72x32 and s3_rule_item_txt_*_{...} 144x32).
# (fill top, fill bottom, outline, glow, glow radius); the glow colour is taken from the original.
RULE_STYLES = {
    ('txt', 'on'):    ((255, 112, 10), (225, 88, 0), (0, 0, 0), (75, 77, 74), 2),        # orange-red
    ('txt', 'off'):   ((128, 126, 124), (128, 126, 124), (39, 39, 39), (60, 60, 60), 2),  # grey
    ('txt', 'hold'):  ((255, 255, 255), (236, 236, 235), (75, 77, 74), (75, 77, 74), 2),  # white
    ('item', 'on'):   ((255, 255, 255), (255, 238, 222), (0, 0, 0), (255, 120, 0), 3),   # white, orange glow
    ('item', 'off'):  ((255, 255, 255), (236, 237, 236), (76, 77, 74), (76, 77, 74), 2),
    ('item', 'hold'): ((255, 253, 239), (255, 199, 46), (21, 21, 21), (21, 21, 21), 2),  # yellow
}

def rule_style(name, orig):
    fam = 'item' if 'rule_item' in name else 'txt'
    state = next((k for k in ('on', 'off', 'hold') if name.endswith('_' + k)), 'off')
    st = list(RULE_STYLES[(fam, state)])
    st[3] = sample_glow(orig) or st[3]
    return tuple(st), (18 if fam == 'txt' else 20)

# in-match challenge info (mahjong_table/s3_tak_chg_info_*, 320x104): two centred lines - the
# header "~Clear Condition~" and the condition itself; white text, grey outline, soft black glow.
CHG_HEADER = '~ Clear Condition ~'
CHG_LINE_CENTRES = (28, 73.5)              # measured on the 104 px tall originals

def render_chg_info(size_wh, text, font_path, size=None):
    W, H = size_wh
    text = text.replace('\\n', '\n')
    header, cond = text.split('\n', 1) if '\n' in text else (CHG_HEADER, text)
    F = Image.new('L', (W, H))
    for line, cy in ((header, CHG_LINE_CENTRES[0]), (cond, CHG_LINE_CENTRES[1])):
        fs = size or 21
        while True:
            f = ImageFont.truetype(font_path, fs)
            r = _text_mask(line, f, W - 24, 0.82)
            if r or fs <= 8: break
            fs -= 1
        m, asc = r or _text_mask(line, f, W - 24, 0.01)
        cap = -f.getbbox('H', anchor='ls')[1]
        base = round(cy * H / 104 + cap / 2)
        F.paste(m, ((W - m.width) // 2, base - asc), m)
    clear = Image.new('RGBA', (W, H))
    def layer(mask, col, alpha=255):
        if alpha < 255: mask = mask.point(lambda v: v * alpha // 255)
        return Image.composite(Image.new('RGBA', (W, H), col + (255,)), clear, mask)
    out = layer(_dilate(F, 4).filter(ImageFilter.GaussianBlur(4)), (0, 0, 0), 230)   # soft dark glow
    out.alpha_composite(layer(_dilate(F, 2), (76, 76, 76)))                           # grey outline
    out.alpha_composite(layer(F, (255, 255, 255)))
    return out

# in-match command labels (mahjong_table/s3_tak_cmd_NN_1 / _2, 64x24) drawn on the grey / orange
# command buttons: _1 = white text with dark-grey outline, _2 = cream text with brown outline.
CMD_STYLES = {'1': ((255, 255, 255), (234, 234, 234), (39, 39, 39), (39, 39, 39), 1),
              '2': ((254, 232, 189), (236, 213, 173), (80, 44, 14), (80, 44, 14), 1)}

BOLD_CONDENSED_FONTS = ['/usr/share/fonts/TTF/DejaVuSansCondensed-Bold.ttf',
                        '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf',
                        '/usr/share/fonts/dejavu/DejaVuSansCondensed-Bold.ttf']

def find_states(base, extra=()):
    hits = [p for p in glob.glob(os.path.join(ROOT, 'work', 'ja', '**', '*.png'), recursive=True)
            if os.path.basename(p)[:-4] == base or
            (os.path.basename(p).startswith(base + '_') and (os.path.basename(p)[len(base) + 1:-4] in STYLES or os.path.basename(p)[len(base) + 1:-4] in extra))]
    return sorted(hits)

def main(argv):
    size, font, preview, charname, helpbtn, title, yaku, yakuman, rule, chg, cmd, args = None, None, False, False, False, False, False, False, False, False, False, []
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
        elif a == '--yakuman': yakuman = True; i += 1
        elif a == '--rule': rule = True; i += 1
        elif a in ('--chg_info', '--chg-info'): chg = True; i += 1
        elif a == '--cmd': cmd = True; i += 1
        elif a in ('-h', '--help'): sys.exit(__doc__)
        else: args.append(a); i += 1
    if not args or len(args) % 2: sys.exit(__doc__)
    font = font or next((p for p in (BOLD_CONDENSED_FONTS if charname else []) + (BOLD_CONDENSED_FONTS if (yaku or rule or cmd) else []) + (CONDENSED_FONTS if helpbtn else []) + FONTS if os.path.exists(p)), None)
    if not font: sys.exit('No font found - pass one with --font /path/to/font.ttf')
    for base, text in zip(args[::2], args[1::2]):
        # Japanese wave dashes aren't in the Latin fonts (they'd draw as a box) -> plain ~
        text = text.replace('\u301c', '~').replace('\uff5e', '~')
        base = os.path.basename(base)
        if base.endswith('.png'): base = base[:-4]
        files = find_states(base, ('1', '2') if cmd else ())
        if not files:
            print(f'!! nothing in work/ja matches "{base}" - check the name'); continue
        pv = []
        for src in files:
            name = os.path.basename(src)[:-4]
            orig = Image.open(src).convert('RGBA')
            if charname:
                img = render_charname(orig.size, text, font, size)
            elif cmd:
                st = CMD_STYLES.get(name.rsplit('_', 1)[-1], CMD_STYLES['1'])
                # draw on a wider canvas at full size, then squeeze sideways if it's too wide
                W0, H0 = orig.size
                wide = render((W0 * 2, H0), text, st, font, size or 19, margin=6)
                bb = wide.getbbox() or (0, 0, 1, 1)
                piece = wide.crop((bb[0], 0, bb[2], H0))
                if piece.width > W0 - 2: piece = piece.resize((W0 - 2, H0), Image.LANCZOS)
                img = Image.new('RGBA', orig.size); img.alpha_composite(piece, ((W0 - piece.width) // 2, 0))
            elif chg:
                img = render_chg_info(orig.size, text, font, size)
            elif rule:
                st, start = rule_style(name, orig)
                img = render(orig.size, text, st, font, size or start)
            elif yakuman:
                img = render_yakuman(orig.size, text, font, size)
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
