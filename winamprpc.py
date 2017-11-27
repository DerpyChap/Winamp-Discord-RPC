
import winamp
import os
import time
import rpc
from tinytag import TinyTag #Amazing for pulling text metadata from various filetypes easily, terrible for album art.
import difflib
import asyncio
import textwrap

w = winamp.winamp()

client_id = '384403264210468874'
RPC = rpc.DiscordRPC(client_id)
RPC.start()

def text_format(songinfo):
    #Discord Rich Embeds don't support newlines, so I'll have to get creative. This also makes it look broken on mobile and on your main profie.
    artist = songinfo[0]
    track = songinfo[1]
    album = songinfo[2]
    if len(artist) >= 32:
        artist = artist[0:24] + "..."
    if len(track) >= 32:
        track = songinfo[1][0:24] + "..."
    if len(album) >= 32:
        album = songinfo[2][0:24] + "..."

    if len(textwrap.fill(track, 16).splitlines()[-1]) <= 24:
        blankspaces = ''.join(['ᅟ' for s in range(24 - len(textwrap.fill(track, 12).splitlines()[-1]))])
        track = track + blankspaces
    if len(textwrap.fill(artist, 16).splitlines()[-1]) <= 24:
        blankspaces = ''.join(['ᅟ' for s in range(24 - len(textwrap.fill(artist, 12).splitlines()[-1]))])
        artist = artist + blankspaces
    #I honestly have no idea what I was doing here but it works well enough somehow.
    return track + artist + album
    

def song_info(filepath, position):
    playlist_pos = position + 1
    try:
        audio = TinyTag.get(filepath)
    except:
        #Try to get the closest matching filename since m3u files replace unicode characters with question marks. (Winamp doesn't save the playlist as .m3u8 >:( ))
        (folder, filename) = os.path.split(filepath)
        files = os.listdir(folder)
        closestmatch = difflib.get_close_matches(filename, files)
        try:
            filepath = folder + "\\" + closestmatch[0]
            audio = TinyTag.get(filepath)
        except IndexError:
            if (filename.startswith(str(playlist_pos))) or (filename.startswith("0" + str(playlist_pos))): #Does checks for a song number at the start of the file JUST IN CASE WE CAN GET A MATCH
                for file in files:
                    if (file.startswith(str(playlist_pos))) or (file.startswith("0" + str(playlist_pos))):
                        filepath = folder + "\\" + file
                        audio = TinyTag.get(filepath)
                        break
            else: #Just in case it STILL doesn't match up. Although, this will be inaccurate at times. PLEASE DON'T USE FILENAMES THAT ONLY CONSIST OF UNICODE CHARACTERS FOR THE LOVE OF GOD PLEASE WINAMP HATES IT.
                closestmatch = [file for file in files if len(file) == len(filename)]
                filepath = folder + "\\" + closestmatch[0]
                audio = TinyTag.get(filepath)
        else: #Give up.
            pass
    try:
        artist = audio.artist
    except:
        artist = "Unknown Artist"
    try:
        song = audio.title
    except:
        song = "Unknown Song"
    try:
        album = audio.album
    except:
        album = "Unknown Album"
    return("👤 " + artist, "🎵 " + song, "💿 " + album)

posbefore = 0
playlistbefore = []
infobefore = {}
details = "No song selected"
while True:
    #Winamp doesn't return the song name OR filepath directly
    playlist_pos = w.dumpList() #This dumps the current playlist AND returns the playlist position as an int
    playlist = w.getTrackList( os.getenv('APPDATA') + "\Winamp\winamp.m3u") #Parse the saved playlist
    if (posbefore != playlist_pos) or (playlistbefore != playlist):
        #Let's only pull new song info if it's actually a new song
        current_time = time.time()
        songpath = playlist[playlist_pos] #Get the current track based on the position in the playlist
        posbefore = playlist_pos
        playlistbefore = playlist
        songinfo = song_info(songpath, playlist_pos) #Time to get that tasty metadata.
        details = text_format(songinfo) #Make the song info look fabulous (Kinda)
    else:
        pass
    #Stuff below checks if it's paused, playing, stopped and sends the song info to the RPC server if something's different
    status = w.getPlayingStatus()
    writtenstatus = status.capitalize()
    activity = {
        "state": "Track",
        "details":  details,
        "assets": {
            "small_text": writtenstatus,
            "small_image": status,
            "large_text": "Winamp",
            "large_image": "cover"
        },
        "party": {
            "size": [playlist_pos + 1, len(playlist)]
        }
    }
    if activity != infobefore:
        RPC.send_rich_presence(activity)
        infobefore = activity
        print(songinfo[0] + " - " + songinfo[1] + " - " + songinfo[2] + " - " + status)
        time.sleep(15) #Rich Presence status has a 15 second cooldown before updating again
    else:
        time.sleep(1)
