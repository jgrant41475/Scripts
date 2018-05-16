Set WshShell = CreateObject("WScript.Shell" ) 
WshShell.Run Chr(34) & "python.exe" & Chr(34) & "NetLibPlayer\NetLibListener.py" & Chr(34), 0 
Set WshShell = Nothing 