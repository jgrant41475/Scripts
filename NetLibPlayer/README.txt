Requirements:
Python 3 - https://www.python.org/downloads/
qBittorrent - https://www.qbittorrent.org/download.php
AutoHotKey - https://autohotkey.com/download/
PSTools - https://technet.microsoft.com/en-us/sysinternals/dd443648.aspx

Installation:
python -m pip install --upgrade pip pyautogui pymsgbox qbittorrent python-qbittorrent
add NetLibPlayer folder to PYTHONPATH
configure NetLibPlayer/config.py

qBittorrent command:
python.exe "C:\PATH\TO\NetLibPlayer\QBittorrent Autodelete.py" --hash="%I" --root="%R" --name="%N" --category="%L"
