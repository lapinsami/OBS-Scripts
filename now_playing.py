# TODO: XDG Base Directory Specification (kinda already implemented)

import os
import io
import dbus
import re
import time
import urllib.request
from PIL import Image
from dbus import DBusException
from xdg.BaseDirectory import xdg_config_home, xdg_data_home
import configparser
import base64

APP_NAME = os.path.join("Vogelchevalier", "OBS-Scripts")


def firstRun():
    if not os.path.exists(os.path.join(xdg_config_home, APP_NAME)):
        os.makedirs(os.path.join(xdg_config_home, APP_NAME))

    if not os.path.exists(os.path.join(xdg_data_home, APP_NAME)):
        os.makedirs(os.path.join(xdg_data_home, APP_NAME))

        config = configparser.ConfigParser()

        config["DEFAULT"] = {
            "player": "strawberry",
            "text_location": os.path.join(xdg_data_home, APP_NAME, "np.txt"),
            "art_location": os.path.join(xdg_data_home, APP_NAME, "art.png")
        }

        config["USER"] = {

        }

        with open(os.path.join(xdg_config_home, APP_NAME, "config.conf"), "w") as cf:
            config.write(cf)


def readConfig():
    config = configparser.ConfigParser()
    config.read(os.path.join(xdg_config_home, APP_NAME, "config.conf"))

    text_location = config["USER"]["text_location"]
    art_location = config["USER"]["art_location"]
    player = config["USER"]["player"]

    return text_location, art_location, player


def writeConfig(key, value):
    config = configparser.ConfigParser()
    config.read(os.path.join(xdg_config_home, APP_NAME, "config.conf"))

    config["USER"][key] = value

    with open(os.path.join(xdg_config_home, APP_NAME, "config.conf"), "w") as cf:
        config.write(cf)


def setupPlayer(default_player):
    bus = dbus.SessionBus()

    players = list()

    for service in bus.list_names():
        if re.match("org.mpris.MediaPlayer2.", service):
            players.append(service.replace("org.mpris.MediaPlayer2.", ""))

    sep = "\n\t"
    print(f"Available players:\n\t{sep.join(players)}")

    selected_player = ""

    while selected_player not in players:
        selected_player = input(f"Select a player (type the name, default {default_player}): ")

        if not selected_player:
            selected_player = default_player

    writeConfig("player", selected_player)

    player = bus.get_object(f"org.mpris.MediaPlayer2.{selected_player}", "/org/mpris/MediaPlayer2")

    return player


def writeTitle(title, filename):
    with open(filename, "w") as f:
        f.write(title)


def getSpotifyAlbumArt(url):
    new_url_prefix = "https://i.scdn.co/image/"
    img_id = url.split("/")[-1]

    urllib.request.urlretrieve(new_url_prefix + img_id, os.path.join(xdg_data_home, APP_NAME, "spotify"))


def writeAlbumArt(source, destination):
    x_max = 500
    y_max = 500

    image = Image.open(source)
    width, height = image.size

    if width == x_max and height == y_max:
        # Already x_max x y_max
        image.save(destination)
        return

    elif width >= x_max or height >= y_max:
        # Over the maximum size
        image.thumbnail((x_max, y_max))

    else:
        # Under the maximum size
        if width == height:
            # Square
            image = image.resize((500, 500), 1)

        elif width > height:
            # Landscape
            new_height = int(500 / width * height)
            image = image.resize((500, new_height), 1)

        elif height > width:
            # Portrait
            new_width = int(500 / height * width)
            image = image.resize((new_width, 500), 1)

    image.save(destination)


def decodeData(data, encoding):
    if encoding == "base64":
        art = io.BytesIO(base64.b64decode(data))
    elif encoding == "base32":
        art = io.BytesIO(base64.b32decode(data))
    elif encoding == "base16":
        art = io.BytesIO(base64.b16decode(data))
    elif encoding == "ascii85":
        art = io.BytesIO(base64.a85decode(data))
    elif encoding == "base85":
        art = io.BytesIO(base64.b85decode(data))
    else:
        art = "default.png"

    return art


def shutdown(text_path, art_path):
    writeTitle(f"", text_path)
    writeAlbumArt("default.png", art_path)

    print("------------------------------------")
    print("Player shut down. Quitting")


def main():
    firstRun()
    text_save_path, art_save_path, player = readConfig()
    player = setupPlayer(player)
    old_song_id = " "

    user_text_save_path = input(f"Path + filename to save the song title to (empty for default: {text_save_path}): ")
    if not user_text_save_path:
        user_text_save_path = text_save_path
    writeConfig("text_location", user_text_save_path)

    user_art_save_path = input(f"Path + filename to save the album art to (empty for default: {art_save_path}): ")
    if not user_art_save_path:
        user_art_save_path = art_save_path
    writeConfig("art_location", user_art_save_path)

    print("------------------------------------")
    print("Started. Ctrl + c to quit")

    while True:
        try:
            metadata = player.Get("org.mpris.MediaPlayer2.Player", "Metadata", dbus_interface="org.freedesktop.DBus.Properties")
        except DBusException:
            shutdown(user_text_save_path, user_art_save_path)
            return

        artist = metadata["xesam:artist"][0] if "xesam:artist" in metadata else ""
        song = metadata["xesam:title"] if "xesam:title" in metadata else ""
        album = metadata["xesam:album"] if "xesam:album" in metadata else ""
        album_art = metadata["mpris:artUrl"] if "mpris:artUrl" in metadata else "default.png"
        album_art = album_art.replace("file://", "")

        song_id = artist + song + album + album_art

        if old_song_id != song_id:
            if album_art.startswith("data:image/"):
                album_art = album_art.partition(",")
                data = album_art[2].replace(' ', '+')
                encoding = album_art[0].partition(";")[2]
                album_art = decodeData(data, encoding)

            elif album_art.startswith("https://open.spotify.com"):
                # Spotify gives broken urls, see
                # https://community.spotify.com/t5/Desktop-Linux/MPRIS-cover-art-url-file-not-found/td-p/4920104
                # And I also have to download the image to use it in writeAlbumArt()
                getSpotifyAlbumArt(album_art)
                album_art = os.path.join(xdg_data_home, APP_NAME, "spotify")

            elif album_art.startswith("https://"):
                urllib.request.urlretrieve(album_art, os.path.join(xdg_data_home, APP_NAME, "https"))
                album_art = os.path.join(xdg_data_home, APP_NAME, "https")

            writeTitle(f"{artist}\n{song}\n{album}", user_text_save_path)
            writeAlbumArt(album_art, user_art_save_path)

            print("------------------------------------")
            print(f"{artist} - {song}, {album}") if artist or song or album else print("Paused")
            print(f"Album art: {album_art}")

        old_song_id = song_id
        time.sleep(0.2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye!")
