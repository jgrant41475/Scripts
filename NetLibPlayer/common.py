from os.path import isfile, isdir, exists
from os import makedirs, scandir
from re import search
from qbittorrent import Client
from shutil import move
from time import strftime, sleep
from pymsgbox import alert
from NetLibPlayer import config


def get_qbt():
    qb = Client(config.qbt_host)
    qb.login(config.qbt_user, config.qbt_pass)
    return qb


def remove_torrent(hash_code):
    qb = get_qbt()
    qb.delete(hash_code)
    qb.logout()


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
        log("Couldn't read torrent.csv")
    finally:
        return name


def add_torrent(magnet, name, category):
    success = False
    qb = get_qbt()
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
                    log("Couldn't read '{}'".format(config.torrents_csv), important=True)
            else:
                log("Torrent '{}' already exists".format(name), important=True)
            log("Added torrent: {} - HASH={}".format(name, torrent_hash))
            success = True
        else:
            log("Invalid magnet link: '{}'".format(magnet), important=True)
    else:
        log("Unable to add magnet link: '{}'".format(magnet), important=True)
    qb.logout()
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
                    log("Permission error: {}".format(error))
        else:
            log("Couldn't create '{}'".format(dst))
    elif isfile(src):
        if dst[-1] == "/":
            dst += src.split("/")[-1]

        dst_path = "/".join(dst.split("/")[:-1])
        if not exists(dst_path):
            makedirs(dst_path)
        try:
            move(src, dst)
        except PermissionError as error:
            log("Permission error: {}".format(error))

    else:
        log("Destination already exists.")


def log(msg, important=False):
    log_msg = "{} :: {}".format(strftime("%m/%d/%Y %I:%M%p"), msg)
    print(log_msg)
    if important:
        alert(msg)
    try:
        with open(config.log_file, "a") as log_file:
            log_file.write(log_msg + "\n")
    except PermissionError:
        pass
