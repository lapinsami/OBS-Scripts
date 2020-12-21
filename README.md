Misc scripts for OBS on Linux. Currently only gets the album art and song info for the currently playing track and saves them to files for OBS to read.

### Requirements
 * Linux (Arch tested)
 * Python (3.9 tested)
 * A music player with MPRIS2 support
 * [requirements.txt](requirements.txt)
#### Usage
 * `python now_playing.py`
 
 ![Running the script](example-images/running.png?raw=true "Running the script")
 
 ![Track info and art in OBS](example-images/obs.png?raw=true "Track info and art in OBS")
 
### Tested players
* [Elisa](https://community.kde.org/Elisa)
* [mpv](https://mpv.io) (artwork does not work, see [antlarr/lua-mpris](https://github.com/antlarr/lua-mpris) for a fix)
* [Spotify](https://www.spotify.com/us/download/linux/)
* [Strawberry](https://www.strawberrymusicplayer.org)

Everything with MPRIS2 support should work

##### License
 * [Zlib](LICENSE)