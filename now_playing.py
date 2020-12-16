# TODO: Handle errors (when the player shuts down for example)
# TODO: XDG Base Directory Specification

import os
import dbus
import re
import time
import urllib.request
from PIL import Image
from xdg.BaseDirectory import xdg_config_home, xdg_data_home
import configparser

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

        with open(os.path.join(xdg_config_home, APP_NAME, 'config.conf'), 'w') as cf:
            config.write(cf)


def readConfig():
    config = configparser.ConfigParser()
    config.read(os.path.join(xdg_config_home, APP_NAME, 'config.conf'))

    text_location = config['USER']['text_location']
    art_location = config['USER']['art_location']
    player = config['USER']['player']

    return text_location, art_location, player


def writeConfig(key, value):
    config = configparser.ConfigParser()
    config.read(os.path.join(xdg_config_home, APP_NAME, 'config.conf'))

    config["USER"][key] = value

    with open(os.path.join(xdg_config_home, APP_NAME, 'config.conf'), 'w') as cf:
        config.write(cf)


def setupPlayer(default_player):
    bus = dbus.SessionBus()

    players = list()

    for service in bus.list_names():
        if re.match('org.mpris.MediaPlayer2.', service):
            players.append(service.replace('org.mpris.MediaPlayer2.', ''))

    sep = '\n\t'
    print(f"Available players:\n\t{sep.join(players)}")

    selected_player = ""

    while selected_player not in players:
        selected_player = input(f"Select a player (type the name, default {default_player}): ")

        if not selected_player:
            selected_player = default_player

    writeConfig("player", selected_player)

    player = bus.get_object(f'org.mpris.MediaPlayer2.{selected_player}', '/org/mpris/MediaPlayer2')

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


def main():
    firstRun()
    text_save_path, art_save_path, player = readConfig()
    player = setupPlayer(player)
    old_url = ""

    filename = input(f"Path + filename to the file where you want to write the window title (default {text_save_path}): ")
    if not filename:
        filename = text_save_path
    writeConfig("text_location", filename)

    album_path = input(f"Path + filename to the file where you want to write the album art (default {art_save_path}): ")
    if not album_path:
        album_path = art_save_path
    writeConfig("art_location", album_path)

    while True:
        metadata = player.Get('org.mpris.MediaPlayer2.Player', 'Metadata', dbus_interface='org.freedesktop.DBus.Properties')
        playing = player.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus', dbus_interface='org.freedesktop.DBus.Properties')

        url = metadata['xesam:url'] if 'xesam:url' in metadata else 'Unknown url'

        if old_url != url:

            artist = metadata['xesam:artist'][0] if 'xesam:artist' in metadata else 'Unknown Artist'
            song = metadata['xesam:title'] if 'xesam:title' in metadata else 'Unknown Song'
            album = metadata['xesam:album'] if 'xesam:album' in metadata else 'Unknown Album'
            album_art = metadata['mpris:artUrl'] if 'mpris:artUrl' in metadata else ''
            album_art = album_art.replace("file://", "")

            if album_art.startswith("https://open.spotify.com"):
                # Spotify gives broken urls, see
                # https://community.spotify.com/t5/Desktop-Linux/MPRIS-cover-art-url-file-not-found/td-p/4920104
                # And I also have to download the image to use it in writeAlbumArt()
                getSpotifyAlbumArt(album_art)
                album_art = os.path.join(xdg_data_home, APP_NAME, "spotify")

            print("--------------------")

            if playing == "Playing":
                print(f"{artist}\n{song}\n{album}")
                writeTitle(f"{artist}\n{song}\n{album}", filename)
                print(album_art)

                if album_art:
                    writeAlbumArt(album_art, album_path)
                else:
                    writeAlbumArt("default.png", album_path)

            else:
                print("Paused")
                writeTitle("", filename)
                writeAlbumArt("default.png", album_path)

            old_url = url

        time.sleep(0.2)


main()
