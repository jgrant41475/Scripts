#SingleInstance force

Gosub, ProgramStart

^!M::startMouseServer()
^!N::startNetPlay()
^!P::ping()
^!A::Run "pythonw.exe" "NetLibPlayer/Add Torrent.py"

startMouseServer()
{
  Run "Start MouseServer.vbs"
}

startNetPlay()
{
  Run "Start NetPlayListener.vbs"
}

ping() {
  RunWait ping -n 4 -w 1000 192.168.0.6
}

ProgramStart:
ping()
startMouseServer()
startNetPlay()