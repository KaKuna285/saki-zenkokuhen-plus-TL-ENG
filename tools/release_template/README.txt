Saki Zenkoku-hen Plus (PS Vita, PCSG00908) - English fan translation  {VERSION}
=========================================================================

WHAT'S TRANSLATED IN THIS VERSION
{NOTES}

REQUIREMENTS
- Your own dump of Saki Zenkoku-hen Plus WITH UPDATE 2.01 (PCSG00908).
  The patch only works on exactly this version; the installer checks this and
  changes nothing if your files don't match.
- Linux/macOS: xdelta3 installed.  Windows: nothing extra (xdelta3.exe is included).

INSTALL - VITA3K
  The game's DATA folder is inside Vita3K's storage:
    Linux:   ~/.local/share/Vita3K/Vita3K/ux0/app/PCSG00908/DATA
    Windows: %APPDATA%\Vita3K\Vita3K\ux0\app\PCSG00908\DATA
             (or the "ux0" folder next to Vita3K.exe for a portable install)
  Make sure update 2.01 is installed in Vita3K first.

  Linux:    ./apply.sh ~/.local/share/Vita3K/Vita3K/ux0/app/PCSG00908/DATA
  Windows:  double-click apply.bat and drag the DATA folder into the window,
            or:  apply.bat "C:\...\PCSG00908\DATA"

  Your original files are kept as *.orig next to them.
  Installing a newer version of this patch later works the same way.

INSTALL - REAL PS VITA (rePatch)
  1. Copy the game's DATA files to your PC. Files from the 2.01 update
     (ux0:patch/PCSG00908/DATA) replace the ones from ux0:app/PCSG00908/DATA.
  2. Run the installer with an output folder:
       ./apply.sh /path/to/DATA  /path/to/output
       apply.bat "C:\path\to\DATA" "C:\path\to\output"
  3. Copy the files from the output folder to  ux0:rePatch/PCSG00908/DATA/

UNINSTALL
  ./apply.sh --restore <DATA folder>     or     apply.bat --restore "<DATA folder>"

MANUAL INSTALL (Delta Patcher etc.)
  Each file in patches/ is a normal xdelta3 patch for the DATA file of the same
  name (e.g. patches/TGA.QPK.xdelta -> DATA/TGA.QPK). Expected checksums are in
  files.txt (name, original sha1, patched sha1) and manifest.json.

CREDITS / LICENCES
  Translation and tools: {AUTHOR}.
  xdelta3.exe is xdelta 3.1.0 by Joshua MacDonald (GPLv2, see xdelta3-COPYING.txt,
  source: https://github.com/jmacd/xdelta-gpl).
  This patch contains no game files; you need your own legal copy of the game.
