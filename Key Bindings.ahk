#SingleInstance force

Gosub, ProgramStart

^!M::startMouseServer()
^!N::startNetPlay()
^!P::ping()
^!A::Run "pythonw.exe" "NetLibPlayer/Add Torrent.py"

startMouseServer()
{
  Run "pythonw.exe" "NetLibPlayer/MouseServer.py"
}

startNetPlay()
{
  Run "pythonw.exe" "NetLibPlayer/NetLibListener.py"
}

ping() {
  RunWait ping -n 4 -w 1000 192.168.0.6
}

ProgramStart:
ping()
startMouseServer()
startNetPlay()