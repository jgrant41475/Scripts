from os.path import isfile, isdir, exists
from argparse import ArgumentParser
from NetLibPlayer.common import log, lookup_torrent_name, QB, Queue
from NetLibPlayer import config


def main():
    parser = ArgumentParser(description="QBittorrent Auto-removal tool")
    parser.add_argument('--hash', type=str, default="TEST_HASH")
    parser.add_argument('--root', type=str)
    parser.add_argument('--name', type=str)
    parser.add_argument('--category', type=str, default=None)

    args = parser.parse_args()

    try:
        torrent_hash = args.hash
        torrent_root = args.root.replace("\\", "/")
        torrent_name = args.name
        torrent_category = args.category.lower()
    except TypeError:
        log("Error: Missing arguments.", important=True, context="QBT Autodelete")

    else:
        log("QBT: name='{}' | hash='{}' | root='{}' | category='{}'"
            .format(torrent_name, torrent_hash, torrent_root, torrent_category), context="QBT Autodelete")

        with QB() as qb:
            qb.delete(torrent_hash)

        if torrent_category:
            name = lookup_torrent_name(torrent_hash) or torrent_name

            if torrent_category == "movie":
                if not exists(torrent_root):
                    log("Torrent doesn't exist: '{}'".format(torrent_root), important=True, context="QBT Autodelete")

                else:
                    path = ""
                    if isfile(torrent_root):
                        parent = "Movies/" + name + "/"
                        if "." not in name and "." in torrent_name:
                            name += "." + torrent_name.split(".")[-1]
                        path = config.media_root + parent + name

                    elif isdir(torrent_root):
                        path = config.media_root + "Movies/" + name

                    queue = Queue(torrent_root, path)
                    if queue.in_queue:
                        log("{} has been added to the queue.".format(path), important=True, context="QBT Autodelete")
                    else:
                        log("All movie torrents finished." if queue.counter > 1 else
                            "{} is ready.".format(path), important=True, context="QBT Autodelete")
            elif torrent_category == "other":
                log("{} is ready.".format(torrent_root))
            else:
                log("Unrecognized category: '{}'".format(torrent_category), important=True, context="QBT Autodelete")
        else:
            log("No Category set for '{}'".format(torrent_name), context="QBT Autodelete")


if __name__ == "__main__":
    main()
