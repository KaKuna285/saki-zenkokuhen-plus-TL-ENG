#!/usr/bin/env python3
"""Saki Zenkoku-hen Plus (PCSG00908) translation workflow.

  python3 tools/saki.py extract <game_dir>
      game_dir = folder containing DATA/ and IDX/ (e.g. ~/.local/share/Vita3K/Vita3K/ux0/app/PCSG00908)
      -> work/tga/      all TGA textures, numbered + named
      -> work/ja/<cat>/ PNG copies of the UI textures, grouped by category (originals, don't edit)
      -> work/csv/      text tables (Shift-JIS)
      -> ui_inventory.csv (one row per UI texture, for tracking translation)

  python3 tools/saki.py build <game_dir>
      Takes every PNG you placed in work/en/ (same file name as in work/ja/, any
      subfolder), converts it back to the original TGA format and rebuilds
      every archive that holds a copy of those textures (TGA.QPK, plus the screen
      bundles in HOTDOG.QPK etc.) into build/DATA/. Untouched entries are copied
      byte-for-byte. Always reads from the original files (.orig backups if present).

  python3 tools/saki.py install <game_dir>
      Backs up each original archive once (as *.orig) and copies build/DATA/* into the game.

  python3 tools/saki.py restore <game_dir>
      Puts all *.orig backups back (undo everything).

  python3 tools/saki.py patch <game_dir> <version> ["release notes"]
      Builds, then creates releases/saki-zenkoku-plus-en-<version>.zip: xdelta patches
      from the original files (*.orig) to the translated ones, checksums, installer
      scripts for Linux/Windows and a player README. Self-tests before packaging.
      Needs xdelta3 (sudo pacman -S xdelta3).
"""
import csv, hashlib, json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hdg, qpk, tgaconv
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lambda *p: os.path.join(ROOT, 'work', *p)

CATS = [  # (category, regex on texture name) - first match wins
    ('story_bubbles', r'^s3_story_\d+_word'),
    ('story_other',   r'^s3_story'),
    ('main_menu',     r'^s3_mm(en|nu)|^s3_ttl|^s3_save|^s3_snd|^s3_wip|^s3_cmw|^s3_plus|^s3_survival'),
    ('common_help',   r'^s3_com'),
    ('mahjong_table', r'^s3_tak|^s3_rst|^s3_rule'),
    ('challenge',     r'^s3_chg|^s3_trmg|^s3_trng'),
    ('online_adhoc',  r'^s3_adh|^s3_room|^s3_entry'),
    ('shop_cards',    r'^s3_shop|^s3_card'),
    ('thumbnails',    r'^s3_thumb'),
    ('character_art', r'^s3_chr(?!.*(tak_name|name))'),
    ('character_names', r'name'),
    ('dummy_unused',  r'^dummy'),
    ('misc',          r'.'),
]
TEXTY = re.compile(r'txt|word|name|ttl|title|btn|msg|help|inf|cmw|warning|mmenu|rule|shop|opt|rst|tak_(start|end|nak)')

def cat_of(name):
    for c, rx in CATS:
        if re.search(rx, name): return c

# Archives that contain textures (directly, or inside HDG screen bundles).
# Later archives override earlier ones in-game (the Plus content lives in EGAPP*).
PACKS = ['TGA', 'OTHER', 'HOTDOG', 'APP0101', 'APP0102', 'APP0103', 'APP0104',
         'EGAPP0101', 'EGAPP0102', 'EGAPP0200']

def is_tga(b): return b[:3] in (b'\x00\x01\x01', b'\x00\x00\x02')
def norm(n): return n.rstrip('_')

def pack_files(data, pk):
    """Original archive paths (the .orig backups if the game has been patched)."""
    qpi, qpkf = (os.path.join(data, pk + ext) for ext in ('.QPI', '.QPK'))
    if os.path.exists(qpkf + '.orig'): qpi, qpkf = qpi + '.orig', qpkf + '.orig'
    return (qpi, qpkf) if os.path.exists(qpkf) else None

def walk_textures(data, names):
    """Yields (pack, entry_index, member_index_or_None, name, raw_entry_bytes, tga_bytes)."""
    for pk in PACKS:
        pf = pack_files(data, pk)
        if not pf: continue
        print(f'  scanning {pk} ...', flush=True)
        _, ents = qpk.read_qpi(pf[0]); nl = names.get(pk, [])
        with open(pf[1], 'rb') as f:
            for i, (off, sz) in enumerate(ents):
                if sz & 0x80000000: continue
                blob = qpk.read_entry(f, off, sz)
                if is_tga(blob):
                    yield pk, i, None, (nl[i - 1] if 0 < i <= len(nl) else f'{pk}_{i}'), blob, blob
                elif blob[:4] == b'HDG\0':
                    for (j, m), n in zip(hdg.members(blob), hdg.names(blob)):
                        if is_tga(m): yield pk, i, j, n, blob, m

def extract(game):
    data, idx = os.path.join(game, 'DATA'), os.path.join(game, 'IDX', 'DATA0.HKT')
    names = qpk.load_names(idx)
    os.makedirs(W(), exist_ok=True)
    json.dump(names, open(W('names.json'), 'w'))
    print('unpacking CSV ...'); qpk.unpack(data, 'CSV', W('csv'), names)
    print('collecting textures from all archives ...')
    latest = {}                          # name -> (tga bytes, where); later archives win
    for pk, i, j, n, _, t in walk_textures(data, names):
        latest[norm(n)] = (t, pk + (f'/{i}' if j is None else f'/{i}:{j}'))
    shutil.rmtree(W('ja'), ignore_errors=True)
    rows = []
    for name in sorted(latest):
        c = cat_of(name)
        if c in ('character_art', 'thumbnails'): continue
        t, where = latest[name]
        try: im, _ = tgaconv.load(t)
        except ValueError: continue
        os.makedirs(W('ja', c), exist_ok=True)
        im.save(W('ja', c, name + '.png'))
        rows.append([name, c, f'{im.size[0]}x{im.size[1]}', 'yes' if TEXTY.search(name) else '', where, '', '', ''])
    with open(os.path.join(ROOT, 'ui_inventory.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['file', 'category', 'size', 'likely_text', 'source', 'japanese', 'english', 'status'])
        w.writerows(rows)
    print(f'{len(rows)} UI textures exported to work/ja, inventory written to ui_inventory.csv')

def build(game):
    data = os.path.join(game, 'DATA')
    names = json.load(open(W('names.json')))
    edits = {}
    for r, _, fs in os.walk(W('en')):
        for f in fs:
            if f.endswith('.png'):
                n = norm(re.sub(r'^\d{4}_', '', f[:-4]))     # old "NNNN_name.png" files still work
                edits[n] = Image.open(os.path.join(r, f)).convert('RGBA')
    print(f'{len(edits)} edited textures; replacing every copy in every archive ...')
    outdir = os.path.join(ROOT, 'build', 'DATA')
    shutil.rmtree(outdir, ignore_errors=True); os.makedirs(outdir)
    seen = set()                          # md5 of originals we replaced -> catch renamed copies
    repl = {}                             # pack -> {entry: bytes or {member: bytes}}
    for pk, i, j, n, blob, t in walk_textures(data, names):
        key = norm(n); h = hashlib.md5(t).hexdigest()
        if key not in edits and h not in seen: continue
        if key not in edits:
            key = seen_name[h]
        im = edits[key]
        orig, fmt = tgaconv.load(t)
        if orig.size != im.size:
            print(f'  WARNING {key}: your PNG is {im.size}, the copy in {pk} is {orig.size} - skipped'); continue
        seen.add(h); seen_name[h] = key
        new = tgaconv.save(im, fmt)
        if j is None: repl.setdefault(pk, {})[i] = new
        else: repl.setdefault(pk, {}).setdefault(i, {})[j] = new
    hdg_cache = {}
    for pk, entries in repl.items():
        qpi, qpkf = pack_files(data, pk)
        tmp = W('_orig'); os.makedirs(tmp, exist_ok=True)
        for a, b in ((qpi, pk + '.QPI'), (qpkf, pk + '.QPK')):
            link = os.path.join(tmp, b)
            if os.path.lexists(link): os.remove(link)
            os.symlink(os.path.abspath(a), link)
        _, ents = qpk.read_qpi(qpi)
        final, count = {}, 0
        with open(qpkf, 'rb') as f:
            for i, v in entries.items():
                if isinstance(v, dict):
                    final[i] = hdg.rebuild(qpk.read_entry(f, *ents[i]), v); count += len(v)
                else:
                    final[i] = v; count += 1
        qpk.pack(tmp, pk, None, outdir, repl_bytes=final)
        print(f'  {pk}: {count} texture copies replaced')
    shutil.rmtree(W('_orig'), ignore_errors=True)
    missing = set(edits) - set(seen_name.values())
    if missing: print('  NOTE: no copy found in the game for:', ', '.join(sorted(missing)))
    print('done -> build/DATA/  (run "install" to copy into the game)')

seen_name = {}

def install(game):
    data = os.path.join(game, 'DATA'); outdir = os.path.join(ROOT, 'build', 'DATA')
    for f in sorted(os.listdir(outdir)):
        dst = os.path.join(data, f)
        if not os.path.exists(dst + '.orig'):
            shutil.copy2(dst, dst + '.orig'); print(f'backed up {f} -> {f}.orig')
        shutil.copy2(os.path.join(outdir, f), dst); print(f'installed {f}')

def restore(game):
    data = os.path.join(game, 'DATA')
    for f in sorted(os.listdir(data)):
        if f.endswith('.orig'):
            shutil.copy2(os.path.join(data, f), os.path.join(data, f[:-5])); print(f'restored {f[:-5]}')

def sha1(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''): h.update(chunk)
    return h.hexdigest()

def patch(game, version, notes=''):
    """Build, then make a release zip of xdelta patches (original 2.01 files -> translation)."""
    import subprocess, tempfile, zipfile, datetime
    xd = shutil.which('xdelta3')
    if not xd: sys.exit('xdelta3 is not installed:  sudo pacman -S xdelta3')
    if not re.fullmatch(r'v?[\w.\-]+', version): sys.exit('version should look like v0.1')
    data = os.path.join(game, 'DATA')
    build(game)
    newdir = os.path.join(ROOT, 'build', 'DATA')
    pkgname = f'saki-zenkoku-plus-en-{version}'
    pkg = os.path.join(ROOT, 'releases', pkgname)
    shutil.rmtree(pkg, ignore_errors=True); os.makedirs(os.path.join(pkg, 'patches'))
    rows, manifest = [], {'game': 'Saki Zenkoku-hen Plus', 'title_id': 'PCSG00908', 'game_version': '2.01',
                          'patch_version': version, 'created': datetime.date.today().isoformat(), 'files': {}}
    print('making xdelta patches ...')
    for f in sorted(os.listdir(newdir)):
        orig = os.path.join(data, f + '.orig')
        if not os.path.exists(orig): orig = os.path.join(data, f)      # game not patched yet
        new = os.path.join(newdir, f)
        out = os.path.join(pkg, 'patches', f + '.xdelta')
        size = os.path.getsize(orig)
        window = min(1 << 31, max(1 << 26, 1 << (size - 1).bit_length()))   # whole file fits in the window
        subprocess.run([xd, '-e', '-9', '-S', 'djw', '-B', str(window), '-f', '-s', orig, new, out], check=True)
        o, n = sha1(orig), sha1(new)
        rows.append(f'{f} {o} {n}')
        manifest['files'][f] = {'original_sha1': o, 'original_size': size, 'patched_sha1': n,
                                'patched_size': os.path.getsize(new), 'patch': f'patches/{f}.xdelta'}
        print(f'  {f}: {os.path.getsize(out) / 1e6:.2f} MB')
    print('verifying: applying the patches to the originals ...')
    with tempfile.TemporaryDirectory(dir=os.path.join(ROOT, 'releases')) as tmp:
        for f, m in manifest['files'].items():
            orig = os.path.join(data, f + '.orig')
            if not os.path.exists(orig): orig = os.path.join(data, f)
            res = os.path.join(tmp, f)
            subprocess.run([xd, '-d', '-f', '-s', orig, os.path.join(pkg, m['patch']), res], check=True)
            if sha1(res) != m['patched_sha1']:
                sys.exit(f'VERIFY FAILED for {f} - release not created')
            os.remove(res)
            print(f'  {f}: OK')
    open(os.path.join(pkg, 'files.txt'), 'w', newline='\n').write('\n'.join(rows) + '\n')
    json.dump(manifest, open(os.path.join(pkg, 'manifest.json'), 'w'), indent=2)
    tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'release_template')
    for fn in ('apply.sh', 'apply.ps1', 'apply.bat'):
        shutil.copy(os.path.join(tpl, fn), pkg)
    os.chmod(os.path.join(pkg, 'apply.sh'), 0o755)
    readme = open(os.path.join(tpl, 'README.txt')).read()
    readme = readme.replace('{VERSION}', version).replace('{AUTHOR}', 'KaKuna285 and contributors')
    readme = readme.replace('{NOTES}', notes or '- (see the release notes)')
    open(os.path.join(pkg, 'README.txt'), 'w', newline='\r\n').write(readme)
    binsrc = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin')
    for fn in ('xdelta3.exe', 'xdelta3-COPYING.txt'):
        if os.path.exists(os.path.join(binsrc, fn)): shutil.copy(os.path.join(binsrc, fn), pkg)
    z = os.path.join(ROOT, 'releases', pkgname + '.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for r, _, fs in os.walk(pkg):
            for fn in fs:
                p = os.path.join(r, fn); zi = zipfile.ZipInfo.from_file(p, os.path.join(pkgname, os.path.relpath(p, pkg)))
                zi.compress_type = zipfile.ZIP_DEFLATED
                if fn == 'apply.sh': zi.external_attr = 0o100755 << 16
                zf.writestr(zi, open(p, 'rb').read())
    print(f'release ready: releases/{pkgname}.zip ({os.path.getsize(z) / 1e6:.1f} MB)')

if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == 'extract': extract(os.path.expanduser(a[1]))
    elif len(a) == 2 and a[0] == 'build': build(os.path.expanduser(a[1]))
    elif len(a) == 2 and a[0] == 'install': install(os.path.expanduser(a[1]))
    elif len(a) == 2 and a[0] == 'restore': restore(os.path.expanduser(a[1]))
    elif len(a) in (3, 4) and a[0] == 'patch': patch(os.path.expanduser(a[1]), a[2], a[3] if len(a) > 3 else '')
    else: sys.exit(__doc__)
