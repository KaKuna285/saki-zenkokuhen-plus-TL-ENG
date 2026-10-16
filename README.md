# Saki Zenkoku-hen Plus (PCSG00908) — English UI translation

Work-in-progress fan translation tools. Phase 1 covers menus and UI.

## What the game's files look like

| File | What it is |
|---|---|
| `DATA/*.QPK` + `*.QPI` | Archives. The QPI holds the index (offset and size per entry). Most entries are `CZL` (zlib) compressed. `tools/qpk.py` unpacks them and rebuilds them **byte-identical** when nothing is changed. |
| `IDX/DATA0.HKT` | Name table for every archive entry. It stores names only (no offsets or sizes), so it doesn't need rebuilding. |
| `TGA.QPK` (7,071 textures) | **Almost all visible Japanese text is baked into images here**: menu buttons, help text, mahjong-table UI, challenge info, and the story-mode speech bubbles (`s3_story_*_word_*`, about 700 of them). |
| `CSV.QPK` | Shift-JIS tables: character names, shop card list, glossary, and so on. Some of them (`reference.csv`, `sysmenu_guide.csv`) look like leftovers from another game on the same engine. |
| `GOF.QPK` | Bitmap fonts `font_a_20.gof` / `font_dbg_22.gof`. ASCII glyphs are present with per-glyph widths, so English should render for any runtime text. |
| `eboot.bin` | Decrypted ELF. Has about 450 UTF-8 strings, mostly debug menus plus a few system dialogs. |
| `HOTDOG.QPK`, `APP*/EGAPP*.QPK` | Animated screens and cut-ins (`HDG` bundles plus `HAM` layouts). The bundles hold their own copies of UI textures, and `build` patches them automatically. |

So phase 1 is **image editing, not script hacking**. No font or pointer work is needed for the UI.

## Requirements

`python` and `python-pillow` (`sudo pacman -S python-pillow`).

## Workflow

```bash
cd ~/Projects/saki-zenkoku-tl
GAME=~/.local/share/Vita3K/Vita3K/ux0/app/PCSG00908

python3 tools/saki.py extract $GAME     # ~1.5 min, ~3 GB in work/
#  work/ja/<category>/<name>.png      original UI textures (reference, don't edit)
#  ui_inventory.csv                   tracking sheet (japanese / english / status columns)

# Put the edited images in work/en/ (same file name, any subfolder),
# either made in GIMP/Krita or with the label helper:
python3 tools/label.py work/ja/main_menu/s3_mmenu_btn_txt_shop_on.png \
        work/en/main_menu/s3_mmenu_btn_txt_shop_on.png "Shop"

python3 tools/saki.py build $GAME       # -> build/DATA/TGA.QPK + TGA.QPI
```

Rules for edited images: keep the **same pixel size** and a transparent background. Paletted
originals are re-quantised to 256 colours automatically.

## Installing and testing in Vita3K

```fish
python3 tools/saki.py build $GAME     # finds every copy of each edited texture
python3 tools/saki.py install $GAME   # backs up originals once (*.orig), copies build/DATA/* in
python3 tools/saki.py restore $GAME   # undo: put the originals back
```
Many screens (main menu, shop, lobby and so on) are animated bundles (`.hdg`) inside `HOTDOG.QPK`, and
the *Plus* edition ships newer versions of some of them in `EGAPP0200.QPK` (for example its own
`mainmenu.hdg`, with slightly different button images). Each bundle carries **its own copy** of
the textures it uses. `extract` exports the newest version of each texture name. `build` replaces **every
texture with that name** in every archive (and any byte-identical copy under another name).
Your PNG must have the same pixel size as the copies it replaces; a warning is printed otherwise.
`build` always reads the `.orig` backups when they exist, so it's safe to run it again and again.

On a real Vita, copy `build/DATA/*` to `ux0:rePatch/PCSG00908/DATA/` instead.

## Making a release (xdelta patch)

```fish
sudo pacman -S xdelta3                                   # once
python3 tools/saki.py patch $GAME v0.1 "- Main menu buttons"
```
This builds, makes xdelta patches **from the original 2.01 files** (`*.orig`) to the translation,
self-tests them, and writes `releases/saki-zenkoku-plus-en-v0.1.zip`. The zip contains the patches,
checksums (`files.txt`, `manifest.json`), installers (`apply.sh` for Linux/macOS, `apply.bat`/`apply.ps1`
plus `xdelta3.exe` for Windows) and a README for players. Every release starts from the originals,
so players only ever need the newest one, and installing it over an older one just works.

## Categories (UI textures exported)

| category | count | notes |
|---|---|---|
| mahjong_table | 1335 | in-match UI, results, rules |
| story_bubbles | 703 | story speech bubbles (this is the story text) |
| shop_cards | 454 | |
| online_adhoc | 412 | ad-hoc and online lobby |
| dummy_unused | 304 | probably unused placeholders, skip |
| main_menu | 215 | **start here** |
| challenge | 199 | challenge mode conditions |
| common_help | 170 | help pages, mode titles |
| character_names | 66 | |
| story_other / misc | 110 | |

## Open questions / next steps
- [ ] In-game test of the rebuilt TGA archive (Cards button)
- [ ] Transcribe the Japanese for `main_menu` + `common_help` into `ui_inventory.csv`
- [ ] Choose a font and style guide for buttons (on / off / hold states differ)
- [ ] Find which runtime-rendered text (CSV tables, eboot strings) actually shows up in game
- [ ] `KS/kslist.akb` is compiled script bytecode. Check whether any story text lives outside the bubble images
