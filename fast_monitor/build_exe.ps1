# Builds onedir FastMonitor next to this script: ..\dist\FastMonitor\FastMonitor.exe
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $here
$pyi = Join-Path $root "bot_env\Scripts\pyinstaller.exe"
if (-not (Test-Path $pyi)) {
    Write-Error "PyInstaller not found at $pyi - install deps: pip install -r fast_monitor\requirements.txt"
    exit 1
}
Set-Location $root
& $pyi --clean --noconfirm (Join-Path $here "fast_monitor.spec")
Write-Host "Output: $root\dist\FastMonitor\FastMonitor.exe"
