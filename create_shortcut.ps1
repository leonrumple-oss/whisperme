# Erstellt die Desktop-Verknuepfung "WisperMe" (inkl. Icon)
$app = $PSScriptRoot
if (-not (Test-Path "$app\wisperme.ico")) {
    & "$app\.venv\Scripts\python.exe" "$app\make_icon.py"
}
$desktop = [Environment]::GetFolderPath('Desktop')
$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut("$desktop\WisperMe.lnk")
$lnk.TargetPath = "$env:WINDIR\System32\wscript.exe"
$lnk.Arguments = """$app\WisperMe starten.vbs"""
$lnk.WorkingDirectory = $app
$lnk.IconLocation = "$app\wisperme.ico,0"
$lnk.Description = "WisperMe – lokales Diktat per Hotkey"
$lnk.Save()
Write-Output "Desktop-Verknuepfung erstellt: $desktop\WisperMe.lnk"
