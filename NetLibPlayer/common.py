from os.path import isfile, isdir, exists
from os import makedirs, scandir, remove
from re import search
from qbittorrent import Client
from qbittorrent.client import LoginRequired
from shutil import move
from time import strftime, sleep
from pymsgbox import alert
from NetLibPlayer import config


class QB:
    def __enter__(self):
        try:
            self.connection = Client(config.qbt_host)
            self.connection.login(config.qbt_user, config.qbt_pass)
            return self.connection
        except ConnectionError:
            log("Error connecting to qBittorrent Web UI", important=True, context="QB")
            raise ConnectionError

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.connection.logout()
        except LoginRequired:
            log("QBT Error: Not logged int!", context="QB")


def lookup_torrent_name(torrent_hash):
    name = ""
    if not isfile(config.torrents_csv):
        return name
    try:
        with open(config.torrents_csv, "r") as file:
            for line in file.readlines():
                h, n = line.strip().split(",")
                if h.lower() == torrent_hash.lower():
                    name = n

    except PermissionError:
        log("Couldn't read torrent.csv", context="lookup_torrent_name")
    finally:
        return name


def add_torrent(magnet, name, category):
    success = False
    with QB() as qb:
        if qb.download_from_link(magnet, category=category) == "Ok.":
            match = search("btih:(.+?)&", magnet)
            if match and match.groups():
                torrent_hash = match.group(1)

                if not name:
                    sleep(3)
                    log_name = qb.get_torrent_files(torrent_hash)
                    if type(log_name) is list and len(log_name) > 0:
                        name = log_name[0]['name'].replace("\\", "/").split("/")[0]

                torrent_name = lookup_torrent_name(torrent_hash)
                if not torrent_name:
                    try:
                        with open(config.torrents_csv, "a") as file:
                            file.write("{},{}\n".format(torrent_hash, name))
                    except PermissionError:
                        log("Couldn't read '{}'".format(config.torrents_csv), important=True, context="add_torrent")
                else:
                    log("Torrent '{}' already exists".format(name), important=True, context="add_torrent")
                log("Added torrent: {} - HASH={}".format(name, torrent_hash), context="add_torrent")
                success = True
            else:
                log("Invalid magnet link: '{}'".format(magnet), important=True, context="add_torrent")
        else:
            log("Unable to add magnet link: '{}'".format(magnet), important=True, context="add_torrent")
    return success


def get_file_list(file, playable=True):
    allowed = config.allowed_extensions if not playable else config.playable_extensions
    temp = []
    for entry in scandir(file):
        if entry.is_dir(follow_symlinks=False):
            temp.extend(get_file_list(entry))
        else:
            if entry.path.split(".")[-1] in allowed:
                temp.append(entry.path)
    return temp


def move_file(src, dst):
    src = src.replace("\\", "/")
    dst = dst.replace("\\", "/")

    if isdir(src) and not exists(dst):
        makedirs(dst)
        if exists(dst):
            for file_list in get_file_list(src, playable=False):
                name = file_list[len(src):].replace("\\", "/")

                if "/" in name and not exists(dst + "/".join(name.split("/")[:-1])):
                    makedirs(dst + "/".join(name.split("/")[:-1]))

                try:
                    move(file_list, dst + name)
                except PermissionError as error:
                    log("Permission error: {}".format(error), context="move_file")
        else:
            log("Couldn't create '{}'".format(dst), context="move_file")
    elif isfile(src):
        if dst[-1] == "/":
            dst += src.split("/")[-1]

        dst_path = "/".join(dst.split("/")[:-1])
        if not exists(dst_path):
            makedirs(dst_path)
        try:
            move(src, dst)
        except PermissionError as error:
            log("Permission error: {}".format(error), context="move_file")

    else:
        log("Destination already exists.", context="move_file")


def log(msg, important=False, context="log"):
    log_msg = "{} :: {} :: {}".format(strftime("%m/%d/%Y %I:%M%p"), context, msg)
    print(log_msg)
    if important:
        alert(msg)
    try:
        with open(config.log_file, "a") as log_file:
            log_file.write(log_msg + "\n")
    except PermissionError:
        pass


class Queue:
    def __init__(self, src, dst):
        self.in_queue = isfile(config.queue_csv)
        self.counter = 0

        if not self.in_queue:
            log("BEGIN NEW QUEUE", context="Queue")
            self.add(src, dst)
            self.loop()
        else:
            self.add(src, dst)

    def loop(self):
        queued = self.pop()
        while queued != "":
            self.counter += 1
            log("[ {} ] :: Moving: {}".format(self.counter, queued), context="Queue")
            split = queued.split("|")
            if type(split) is list and len(split) == 2:
                move_file(split[0], split[1])
            else:
                log("Invalid queue: '{}'".format(queued), important=True, context="Queue")
            queued = self.pop()
        remove(config.queue_csv)

    @staticmethod
    def add(src, dst):
        log("Queuing: " + src, context=__name__)
        try:
            with open(config.queue_csv, "a") as file:
                file.write("{}|{}\n".format(src, dst))
        except PermissionError:
            log("Couldn't access queue file. | {}".format(src), important=True, context="Queue")

    @staticmethod
    def pop():
        popped = ""
        if not isfile(config.queue_csv):
            return popped
        try:
            with open(config.queue_csv, "r") as file:
                queue = file.readlines()

            popped = queue[0]
            with open(config.queue_csv, "w") as file:
                file.write("".join(queue[1:]) if len(queue) > 1 else "")

        except PermissionError:
            log("Couldn't access queue file.", important=True, context="Queue")
        except FileNotFoundError:
            log("Queue file not found.", important=True, context="Queue")
        finally:
            return popped.strip()
