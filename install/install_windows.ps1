<#
  VOID — Windows Installer (PowerShell)
  Aufruf (PowerShell):
    irm https://raw.githubusercontent.com/IrsanAI/void/main/install/install_windows.ps1 | iex
#>

$ErrorActionPreference = "Stop"

function Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Warn($msg) { Write-Host $msg -ForegroundColor Yellow }
function Fail($msg) { Write-Host $msg -ForegroundColor Red }

$InstallDir = Join-Path $HOME "games\void"
$RepoUrl = "https://github.com/IrsanAI/void.git"
$BinDir = Join-Path $HOME "bin"
$ShimPath = Join-Path $BinDir "void.ps1"

Write-Host ""
Write-Host "VOID — Windows Edition Installer" -ForegroundColor Magenta
Write-Host "---------------------------------"

Info "[1/5] Prüfe Voraussetzungen..."
if (-not (Get-Command python -ErrorAction SilentlyContinue) -and -not (Get-Command python3 -ErrorAction SilentlyContinue)) {
  Fail "Python wurde nicht gefunden. Bitte zuerst Python 3 installieren: https://python.org"
  exit 1
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Fail "git wurde nicht gefunden. Bitte zuerst Git installieren: https://git-scm.com"
  exit 1
}
Ok "Python und git vorhanden."

Info "[2/5] Hole/aktualisiere Repository..."
if (Test-Path (Join-Path $InstallDir ".git")) {
  Push-Location $InstallDir
  git pull --ff-only | Out-Null
  Pop-Location
  Ok "Repository aktualisiert."
} else {
  New-Item -Path (Split-Path $InstallDir -Parent) -ItemType Directory -Force | Out-Null
  if (Test-Path $InstallDir) {
    $hasContent = (Get-ChildItem -Path $InstallDir -Force -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0
    if ($hasContent) {
      $BackupDir = "${InstallDir}_backup_$(Get-Date -Format yyyyMMdd_HHmmss)"
      Move-Item $InstallDir $BackupDir
      Warn "Bestehender Ordner wurde gesichert nach: $BackupDir"
    }
  }
  git clone --depth=1 $RepoUrl $InstallDir | Out-Null
  Ok "Repository geklont."
}

Info "[3/5] Prüfe Kerndateien..."
$required = @(
  "game/void_launcher.py",
  "game/void_server.py",
  "game/void_client.py",
  "game/void_relay.py"
)
foreach ($r in $required) {
  $p = Join-Path $InstallDir $r
  if (-not (Test-Path $p)) {
    Fail "Datei fehlt: $p"
    exit 1
  }
}
Ok "Kerndateien vorhanden."

Info "[4/5] Lege Startbefehl 'void' an..."
New-Item -Path $BinDir -ItemType Directory -Force | Out-Null
@"
param([Parameter(ValueFromRemainingArguments=`$true)] [string[]]`$Args)
`$py = (Get-Command python -ErrorAction SilentlyContinue)
if (-not `$py) { `$py = (Get-Command python3 -ErrorAction SilentlyContinue) }
if (-not `$py) { Write-Host 'Python fehlt.' -ForegroundColor Red; exit 1 }
if (`$Args.Length -gt 0 -and `$Args[0] -eq "doctor") {
  if (`$Args.Length -gt 1) { `$rest = `$Args[1..(`$Args.Length-1)] } else { `$rest = @() }
  & `$py.Source "$InstallDir\game\void_doctor.py" @rest
} else {
  & `$py.Source "$InstallDir\game\void_launcher.py" @Args
}
"@ | Set-Content -Path $ShimPath -Encoding UTF8

$profileLine = "`$env:PATH = `"$BinDir;`$env:PATH`""
if (-not (Test-Path $PROFILE)) { New-Item -Path $PROFILE -ItemType File -Force | Out-Null }
$profileContent = Get-Content $PROFILE -ErrorAction SilentlyContinue
if (-not ($profileContent -match [regex]::Escape($BinDir))) {
  Add-Content -Path $PROFILE -Value "`n# VOID installer PATH"
  Add-Content -Path $PROFILE -Value $profileLine
  Ok "PATH-Eintrag im PowerShell-Profil ergänzt."
} else {
  Ok "PATH-Eintrag bereits vorhanden."
}

Info "[5/5] Führe Installer-Selftest + lokalen Smoke-Test aus..."
$pyExe = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $pyExe) { $pyExe = (Get-Command python3 -ErrorAction SilentlyContinue) }
& $pyExe.Source "$InstallDir\install\installer_selftest.py"
& $pyExe.Source "$InstallDir\game\void_smoke_test.py"

Write-Host ""
Ok "Installation abgeschlossen."
Write-Host "Starten mit:  python $InstallDir\game\void_launcher.py"
Write-Host "Oder (nach neuem Terminal):  void"
