' Startet WisperMe ohne Konsolenfenster
Set WshShell = CreateObject("WScript.Shell")
Dim appDir
appDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\") - 1)
WshShell.Run """" & appDir & "\.venv\Scripts\pythonw.exe"" """ & appDir & "\app.py""", 0, False
