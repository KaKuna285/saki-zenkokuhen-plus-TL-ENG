# Saki Zenkoku-hen Plus (PS Vita, PCSG00908) — English fan translation

An English patch for **Saki Zenkoku-hen Plus** (update 2.01), plus the tools used to make it, so
anyone can pick up the work and continue it.

**Current version: v1.01.** Download it from the
[Releases page](https://github.com/KaKuna285/saki-zenkokuhen-plus-TL-ENG/releases).

## Translation status

| Part of the game | Status |
|---|---|
| Main menu and mode select | Done |
| Help bar and help pages, mode titles | Done |
| Shop / cards | UI elements done, cards not yet |
| Music | Done |
| Online / ad-hoc lobby | Done |
| Rules screen | Done |
| Character names (romaji, given name first) | Done |
| Training screens (stats, abilities) | Done |
| In-match UI (commands, challenge info, cursor, yakus and end texts) | Mostly done, some elements left |
| Challenges including network challenges| Not yet |
| Story mode (speech bubbles, about 700 images) | Not yet |
| Staff roll (a video, `MOVIE.QPK`) | Not yet |
| Save-data and online messages | Done |


Yaku names use romaji (Riichi, Tanyao, Kokushi Musou …) and "Han" rather than english translations.

Many items could also use some QA and touching up.

## For players: installing the patch

You need your own dump of the game **with update 2.01**. The patch only works on that exact
version; the installer checks this and changes nothing if your files don't match.

1. Download the newest `saki-zenkoku-plus-en-vX.Y.zip` from Releases and unzip it.
2. Run the installer on the game's `DATA` folder:
   - **Vita3K, Linux:** `./apply.sh ~/.local/share/Vita3K/Vita3K/ux0/app/PCSG00908/DATA`
   - **Vita3K, Windows:** double-click `apply.bat` and drag the `DATA` folder into the window
     (usually `%APPDATA%\Vita3K\Vita3K\ux0\app\PCSG00908\DATA`)
   - **Real PS Vita:** run the installer with an output folder
     (`./apply.sh <DATA> <output>`), then copy the output to `ux0:rePatch/PCSG00908/DATA/`

The installer also patches `eboot.bin` (music list names, save and online messages) if your
copy matches the one the patch was made from; if not, it says "skipped eboot.bin" and that
text stays Japanese. Your original files are kept as `*.orig`. To uninstall: `./apply.sh --restore <DATA folder>`.
A newer release installs straight over an older one. The `README.txt` inside the zip has the
full instructions.

## For translators: how it works

Almost all Japanese text in this game is **baked into images** (textures), so translating it is
image editing, not script hacking. The tools here extract every texture as a PNG, let you
draw English versions in the game's style, and put them back.

### Requirements

Linux (developed on CachyOS/Arch with the fish shell):

```fish
sudo pacman -S python-pillow xdelta3 ttf-dejavu
```

### Workflow

```fish
cd ~/Projects/saki-zenkoku-tl
set -U GAME ~/.local/share/Vita3K/Vita3K/ux0/app/PCSG00908   # once (bash: GAME=...)

python3 tools/saki.py extract $GAME    # ~1.5 min, ~3 GB: originals as PNGs in work/ja/<category>/
# make English images in work/en/ (same file name, any subfolder): label.py or GIMP/Krita
python3 tools/saki.py build $GAME      # puts every edited texture back -> build/DATA/
python3 tools/saki.py install $GAME    # copies into the game (backs up originals as *.orig once)
python3 tools/saki.py restore $GAME    # undo: put the originals back
```

Rules for edited images: same pixel size as the original (exceptions can be listed in
`resize_ok.txt`) and a transparent background. Paletted originals are re-quantised
automatically. `build` always starts from the `.orig` backups, so it is safe to run as often as
you like.

### label.py — English labels in the game's styles

Give the texture name (without `_on`/`_off`/`_hold`) and the English text. The tool finds every
state of that image in `work/ja/`, draws each one in the matching style and saves it to `work/en/`:

```fish
python3 tools/label.py s3_mmenu_btn_txt_team "Team"
python3 tools/label.py --preview s3_mmenu_btn_txt_shop "Shop"   # also writes a before/after image
```

| Option | Used for |
|---|---|
| *(none)* | menu buttons: `_on`, `_off`, `_hold`, `_disable`, `_invalid` states |
| `--charname` | character name plates (`s3_chrNN_tak_name`) |
| `--help_btn` | help-bar buttons (`s3_com_help_btn_txt_NN`) |
| `--title` | mode titles (`s3_com_mode_title_txtNN`), text after `~` drawn smaller |
| `--yaku` | result-screen yaku lines (`s3_rst_yaku01`–`28`) |
| `--yakuman` | gold yakuman banners (`s3_rst_yaku32`–`44`) |
| `--rule` | rules screen (`s3_rule_txt*`, `s3_rule_item_txt_*`) |
| `--chg_info` | in-match challenge conditions (`s3_tak_chg_info_*`) |
| `--cmd` | in-match commands (`s3_tak_cmd_NN`, both `_1` and `_2`) |

Other options: `--size N`, `--font file.ttf`. Use `\n` in the text for two lines.
`python3 tools/label.py` with no arguments prints the full help.

### Text inside the game program (eboot.bin)

A little text is not an image but a string inside `eboot.bin`: the music room list, the
save-data messages and the online lobby messages. Translations live in `text/eboot.tsv`
(Japanese, tab, English, tab, note; `\n` is a line break). `build` applies them
automatically and writes `build/eboot.bin`; `install` copies it into the game.

```fish
python3 tools/eboot.py check $GAME    # does every line fit and get found?
python3 tools/eboot.py dump $GAME     # list all Japanese strings -> work/eboot_strings.tsv
```

English must fit in the bytes of the Japanese (a Japanese character is 3 bytes, a letter 1)
plus any free space after it, and `%s`/`%d` codes must stay the same. `check` tells you.

Complex screens (for example the training ability pages, `s3_trng_ability_info_NN`) were made in
GIMP with DejaVu Sans Bold.

### Making a release

```fish
python3 tools/saki.py patch $GAME v1.1 "What's new in this version"
```

This builds, makes xdelta patches from the original 2.01 files to the translation, self-tests
them and writes `releases/saki-zenkoku-plus-en-v1.1.zip`, with installers for Linux/macOS
(`apply.sh`) and Windows (`apply.bat`/`apply.ps1` plus `xdelta3.exe`). Every release patches from
the originals, so players only ever need the newest one.

## What's left, and where to find it

| Category in `work/ja/` | What's in it |
|---|---|
| `story_bubbles` | story speech bubbles (`s3_story_*_word_*`): this *is* the story text |
| `challenge` | challenge mode conditions (`s3_chg_*`); training (`s3_trng_*`, `s3_trmg_*`) is done |
| `mahjong_table` | in-match UI; a few elements are still Japanese |
| `shop_cards` | shop and card related, cards are still in Japanese |
| `dummy_unused` | probably unused placeholders, can be skipped |
| `DATA/MOVIE.QPK` | two MP4 videos (960×544, H.264): the opening and the staff roll; the credits are baked into the video |

Open questions:
- Find out which runtime-rendered text in the CSV tables actually shows up in game. (The eboot
  strings players see are in `text/eboot.tsv`; `tools/eboot.py dump` lists the rest, mostly debug menus.)
- `KS/kslist.akb` is compiled script bytecode. Check whether any story text lives outside the
  bubble images.

## Technical notes on the game's files

| File | What it is |
|---|---|
| `DATA/*.QPK` + `*.QPI` | Archives. The QPI is the index (offset and size per entry); most entries are `CZL` (zlib) compressed. `tools/qpk.py` unpacks them and rebuilds them byte-identically when nothing changes. |
| `IDX/DATA0.HKT` | Name table for every archive entry (names only, so it never needs rebuilding). |
| `TGA.QPK` | About 7,000 textures: almost all visible Japanese text. |
| `HOTDOG.QPK`, `APP*.QPK`, `EGAPP*.QPK` | Animated screens (`HDG` bundles). Each bundle carries its own copies of the textures it uses; the *Plus* edition's newer versions are in `EGAPP0200.QPK`. `build` patches every copy by name. |
| `CSV.QPK` | Shift-JIS tables (character names, shop card list, glossary …). |
| `GOF.QPK` | Bitmap fonts with ASCII glyphs, so English works for any runtime text. |
| `eboot.bin` | About 600 UTF-8 strings, mostly debug menus; the player-visible ones are in `text/eboot.tsv`. |

Fan project, not affiliated with the game's publishers. This repo contains only tools and
instructions, no game files: you need your own copy of the game.
