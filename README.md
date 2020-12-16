Misc scripts for OBS on Linux. Currently only gets the album art and song info for the currently playing track and saves them to files for OBS to read.

### Requirements
 * Linux (Arch tested)
 * Python >= 3.9, might work on older python3 versions, haven't tested
 * python-dbus
 * python-pyxdg
 * See the imports for python packages
 * A music player with MPRIS2 support
 
#### Usage
 * `python now_playing.py`
 
 ![Running the script](example-images/running.png?raw=true "Running the script")
 
 ![Track info and art in OBS](example-images/obs.png?raw=true "Track info and art in OBS")
 
### Tested players
Everything with MPRIS2 support should work
* Strawberry
* Spotify

##### License
 * [Zlib](LICENSE)