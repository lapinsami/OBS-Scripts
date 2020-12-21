#!/usr/bin/env python
# TODO: XDG Base Directory Specification (kinda already implemented)

import os
import io
import dbus
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
            "player": "",
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
        if service.startswith("org.mpris.MediaPlayer2."):
            players.append(service.replace("org.mpris.MediaPlayer2.", ""))

    players = sorted(players)

    if not default_player:
        default_player = players[0]

    elif default_player not in players:
        print(f"Default player {default_player} not running")
        default_player = players[0]

    # Generate short strings for each player
    player_shorts = list()

    for player in players:
        player_short = ""

        for i in range(len(player)):
            if not player[i].isnumeric():
                player_short += player[i]

            if player_short not in player_shorts:
                player_shorts.append(player_short)
                break

            elif i == len(player) - 1:
                player_shorts.append(None)
                break

    # Print available players
    tab = "\t"
    print(f"Available players:")
    for i, short in enumerate(player_shorts):
        print(f"{i + 1}.{tab}{players[i].replace(short, '[' + short + ']', 1)}")

    # Get input
    selected_player = ""
    while selected_player not in players:
        user_input = input(f"\nSelect a player (default {default_player})\n> ")

        if not user_input:
            selected_player = default_player

        # Selecting with name
        elif user_input in players:
            selected_player = user_input

        # Selecting with shorthand
        elif user_input in player_shorts:
            selected_player = players[player_shorts.index(user_input)]

        # Selecting with number
        elif user_input.isnumeric():
            user_input = int(user_input)
            if 1 <= user_input <= len(players):
                selected_player = players[user_input - 1]

    print("\033[92m" + f"[OK] Selected {selected_player} as the player" + "\033[0m")
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


def main():
    firstRun()
    text_save_path, art_save_path, player = readConfig()
    player = setupPlayer(player)
    old_song_id = " "

    user_text_save_path = input(f"Path + filename to save the song title to\nEmpty for default: {text_save_path}\n> ")
    if not user_text_save_path:
        user_text_save_path = text_save_path
    writeConfig("text_location", user_text_save_path)
    print("\033[92m" + f"[OK] Saving to {user_text_save_path}" + "\033[0m")

    user_art_save_path = input(f"Path + filename to save the album art to\nEmpty for default: {art_save_path}\n> ")
    if not user_art_save_path:
        user_art_save_path = art_save_path
    writeConfig("art_location", user_art_save_path)
    print("\033[92m" + f"[OK] Saving to {user_art_save_path}" + "\033[0m")

    print("-----------------" + "\033[95m" + "Started. Ctrl + c to quit" + "\033[0m" + "-----------------")

    while True:
        try:
            metadata = player.Get("org.mpris.MediaPlayer2.Player", "Metadata", dbus_interface="org.freedesktop.DBus.Properties")
        except DBusException:
            print("\033[93m" + "[ERROR] Player shut down. Quitting" + "\033[0m")
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

            print(f"{artist} - {song}\n{album}") if artist or song or album else print("Paused")
            print(f"Album art: {album_art}")
            print("-----------------------------------------------------------")

        old_song_id = song_id
        time.sleep(0.2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye!")
