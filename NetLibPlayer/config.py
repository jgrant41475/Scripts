ip_address = "192.168.0.5"      # IP address of host machine
mouse_server_port = 5050        # Port number that MouseServer will listen on
netplay_port = 5051     # Port number that NetLibListener will listen on

qbt_host = "http://localhost:8081/"     # qBittorrent Web UI fully qualified URL
qbt_user = "anon"       # qBittorrent Web UI username
qbt_pass = "password"       # qBittorrent Web UI password

allowed_extensions = ["srt", "mp4", "avi", "mkv", "pdf", "txt"]     # File extensions that will be transferred.
playable_extensions = ["mp4", "avi", "mkv"]     # File extensions that VLC can handle

media_root = "M:/PATH/TO/Media/"     # Root folder that Movie/Show categories will be moved to
vlc_path = "C:/PATH/TO/VideoLAN/VLC/vlc.exe"        # Path to VLC executable
log_file = "C:/PATH/TO/NetLibPlayer/logs.txt"       # Path to log file
psshutdown = "C:/PATH/TO/PSTools/psshutdown.exe"    # Path to PSShutdown executable
torrents_csv = "C:/PATH/TO/NetLibPlayer/torrents.csv"       # Path to torrents CSV file
queue_csv = "C:/PATH/TO/NetLibPlayer/NetLibPlayer/queue.csv"     # Path to queueing file
