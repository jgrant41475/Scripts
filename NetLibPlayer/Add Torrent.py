from pymsgbox import prompt, confirm
from NetLibPlayer.common import add_torrent, log


if __name__ == "__main__":
    magnet = prompt("Magnet Link:", "Add Torrent")
    if magnet:
        name = prompt("Torrent Name:", "Add Torrent")
        cat = confirm("Set category to:", "Add Torrent", ["Other", "Movie", "Show", "Cancel"]) or "Other"

        if not name or cat == "Cancel":
            log("Canceled. {}".format(magnet), important=True, context="Add Torrent")

        elif not add_torrent(magnet, name, cat):
            log("An error occurred. | Magnet='{}' | Name='{}'".format(magnet, name),
                important=True, context="Add Torrent")
