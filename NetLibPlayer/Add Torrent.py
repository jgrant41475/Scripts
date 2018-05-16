from pymsgbox import prompt, confirm, alert
from NetLibPlayer.common import add_torrent


if __name__ == "__main__":
    magnet = prompt("Magnet Link:", "Add Torrent")
    if magnet:
        name = prompt("Torrent Name:", "Add Torrent")
        cat = confirm("Set category to:", "Add Torrent", ["Other", "Movie", "Show"]) or "Other"

        if not add_torrent(magnet, name, cat):
            alert("An error occurred.", "Add Torrent")
