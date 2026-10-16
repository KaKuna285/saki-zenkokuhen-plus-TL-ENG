# Saki Zenkoku-hen Plus (PCSG00908, v2.01) - English patch installer for Windows.
# Run via apply.bat (double-click it, or from a terminal):
#   apply.bat "C:\path\to\PCSG00908\DATA"                 patch the game in place (backs up originals as *.orig)
#   apply.bat "C:\path\to\PCSG00908\DATA" "C:\out"        write patched files to C:\out instead (rePatch on a real Vita)
#   apply.bat --restore "C:\path\to\PCSG00908\DATA"       undo: put the *.orig backups back
$a = $args[0]; $b = $args[1]   # plain \$args so '--restore' is not parsed as a parameter
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$xd = Join-Path $here 'xdelta3.exe'
$files = Get-Content (Join-Path $here 'files.txt') | Where-Object { $_.Trim() } | ForEach-Object {
    $p = $_ -split '\s+'; [pscustomobject]@{ Name = $p[0]; Orig = $p[1]; New = $p[2] } }
function Sha($f) { (Get-FileHash -Algorithm SHA1 -LiteralPath $f).Hash.ToLower() }

if ($a -eq '--restore' -or $a -eq 'restore') {
    $b = $b.Trim('"').TrimEnd('\\')
    foreach ($f in $files) { $o = Join-Path $b "$($f.Name).orig"
        if (Test-Path $o) { Copy-Item -Force $o (Join-Path $b $f.Name); "restored $($f.Name)" } }
    exit 0
}
if (-not $a) { $a = Read-Host 'Drag the game''s DATA folder here and press Enter' }
$data = $a.Trim('"').TrimEnd('\\'); $out = if ($b) { $b.Trim('"') } else { $null }
"Checking your game files ..."
$base = @{}
foreach ($f in $files) {
    $t = Join-Path $data $f.Name
    $src = if (Test-Path "$t.orig") { "$t.orig" } else { $t }
    if (-not (Test-Path $src)) { "MISSING: $t"; exit 1 }
    $h = Sha $src
    if ($h -ne $f.Orig) { "WRONG VERSION: $($f.Name) does not match Saki Zenkoku-hen Plus v2.01 (sha1 $h)"; 'Nothing was changed.'; exit 1 }
    $base[$f.Name] = $src
}
if ($out) { New-Item -ItemType Directory -Force $out | Out-Null }
foreach ($f in $files) {
    $t = Join-Path $data $f.Name; $src = $base[$f.Name]
    if (-not $out -and $src -eq $t) { Copy-Item -Force $t "$t.orig"; $src = "$t.orig" }
    $dest = Join-Path $(if ($out) { $out } else { $data }) $f.Name
    "patching $($f.Name) ..."
    & $xd -d -f -s $src ([IO.Path]::Combine($here, "patches", "$($f.Name).xdelta")) "$dest.tmp"
    if ($LASTEXITCODE -ne 0 -or (Sha "$dest.tmp") -ne $f.New) { Remove-Item -Force -ErrorAction SilentlyContinue "$dest.tmp"; "PATCH FAILED for $($f.Name)"; exit 1 }
    Move-Item -Force "$dest.tmp" $dest
}
'Done! The English patch is installed.'
