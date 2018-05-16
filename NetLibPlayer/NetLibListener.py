from socket import socket, error as sock_error
from os import scandir
from subprocess import run
from NetLibPlayer import config
from NetLibPlayer.common import get_file_list, log, add_torrent


class NetLibListener:
    def __init__(self, host=config.ip_address, port=config.netplay_port):
        self.sock = socket()

        # Attempts to bind socket
        try:
            self.sock.bind((host, port))
        except OSError:
            # self.sock_error = self.ERROR_BIND
            self.sock.close()
            return

        # Listens for one connection attempt at a time
        self.sock.listen(1)
        log("Listening on interface: " + host + ":" + str(port))

        # Continuously listen for connection attempts, and calls _on_connect() when one is made
        while True:
            conn, addr = self.sock.accept()
            log("Connection with " + addr[0] + ":" + str(addr[1]) + " established")
            self._on_connect(conn)

    @staticmethod
    def _on_connect(conn):
        """Connection with client has been established"""
        try:
            data = str(conn.recv(4096), "utf-8").strip().split(" ")
            args = ""

            file = ""
            root = ""
            new_name = ""
            cat = ""
            magnet = ""
            add = False
            lib = False
            play = False

            for cmd in data:
                if "=" in cmd:
                    cmd_list = cmd.split("=")
                    com, args = cmd_list[0], "=".join(cmd_list[1:]).replace("`", " ")
                else:
                    com = cmd

                if com == "root":
                    root = args.strip('"').strip("'")
                elif com == "file":
                    file = args.replace("`", " ")
                elif com == "list":
                    lib = True
                elif com == "play":
                    play = True
                elif com == "add":
                    add = True
                elif com == "cat":
                    cat = args
                elif com == "name":
                    new_name = args
                elif com == "link":
                    magnet = args

            if lib and root:
                [conn.send(str.encode("{}@{}\n".format(cat.path.split("\\")[-1],
                                                       "|".join(sorted(get_file_list(cat.path))))))
                 for cat in scandir(root)]

            elif play and file.split(".")[-1] in config.allowed_extensions:
                run([config.vlc_path, file, "-f"])

            elif add and cat and new_name and magnet:
                conn.send(b'OK' if add_torrent(magnet, new_name, cat) else b'BAD')

        except sock_error as error:
            log("Error: " + str(error))

        finally:
            conn.close()


if __name__ == "__main__":
    NetLibListener()
