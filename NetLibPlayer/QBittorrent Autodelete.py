from os.path import isfile
from argparse import ArgumentParser
from pymsgbox import prompt
from NetLibPlayer.common import move_file, remove_torrent, log, lookup_torrent_name
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
        torrent_category = args.category
    except TypeError:
        log("Error: Missing arguments.", important=True)

    else:
        remove_torrent(torrent_hash)

        if torrent_category:
            new_name = lookup_torrent_name(torrent_hash)
            if not new_name:
                new_name = prompt("Rename '{}' to:".format(torrent_name), "NetPlay", default=torrent_name)
                if not new_name:
                    new_name = torrent_name

            if isfile(torrent_root + torrent_name):
                folder = torrent_root + ".".join(new_name.split(".")[:-1]) + "/"
                move_file(torrent_root + torrent_name, folder + torrent_name)
                torrent_root = folder

            if torrent_category == "Other":
                new_torrent = torrent_root
                if new_name:
                    new_torrent = "{}/{}".format("/".join(torrent_root.split("/")[:-1]), new_name)
                    move_file(torrent_root, new_torrent)
                log("Download complete: '{}'".format(new_torrent), important=True)

            elif torrent_category == "Movie":
                new_torrent = config.media_root + "Movies/" + new_name
                move_file(torrent_root, new_torrent)
                log("{} is ready".format(new_torrent), important=True)

            else:
                log("Unrecognized category: '{}'".format(torrent_category), important=True)
        else:
            log("No Category set for '{}'".format(torrent_name))


if __name__ == "__main__":
    main()
