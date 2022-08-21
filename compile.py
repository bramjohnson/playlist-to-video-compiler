#!/usr/bin/env python3

import argparse
import os
import shutil
import ffmpeg
import utils
from utils import Tracklist

TITLE = "out"
AUDIO_BITRATE = "320k"
VIDEO_BITRATE = "4000K"

# Initialize parse
parser = argparse.ArgumentParser(description="Generate a video from music files.")
parser.add_argument("-s", "--silence", nargs=2, metavar=('START', 'END'),
    help="removes silence from START seconds at the start, and from END seconds at the end.", type=int, default=[4,4])
parser.add_argument("-n", "--normalize", action='store_true', help="normalizes the audio of the output")
parser.add_argument("-f", "--fit", action='store_true', help="fits the thumbnail into a 1920x1080 size")
parser.add_argument("-d", "--data", action='store_true', help="Create a tracklist and captions file when compiling.")
parser.add_argument("-t", "--thumbnail", help="Makes the image for the video THUMBNAIL", type=str, required=False)
parser.add_argument("-i", "--input", help="Either the path of the src folder or an m3u file.", type=str, required=True)
parser.add_argument("-o", "--output", help="An output folder where any videos/files will be placed.", type=str, required=False, default="./")

# Initialize args
args = parser.parse_args()

# Initialize file collections
output_fc = []
util_fc = [] # if collecting util files like big_audio is ever useful.

def main():
    utils.cleanup()

    thumbnail = args.thumbnail

    # ensure correct args
    if (not os.path.isdir(args.output)):
        return

    # import songs from various sources
    songs = []
    ### import from directory
    if (os.path.isdir(args.input)):
        for root, dirs, files in os.walk(args.input):
            for name in files:
                if (name.endswith(".mp3")):
                    songs.append(os.path.join(root, name))
    ### import from m3u playlist file
    elif (os.path.isfile(args.input) and args.input.endswith(".m3u")):
        playlist = open(args.input, 'r')
        for song in playlist:
            songs.append(song.rstrip())
    elif (os.path.isfile(args.input) and args.input.endswith(".m3u8")):
        playlist = open(args.input, 'r', encoding='utf-8-sig')
        for song in playlist:
            if (not song.startswith("#")):
                songs.append(song.rstrip())
    ### import from nowhere at all
    else:
        return

    # Localize all songs for editing purposes
    local_songs = []
    if (not os.path.exists('./tracklist/')):
        os.mkdir('./tracklist/')
    for song in songs:
        new_song = "./tracklist/" + os.path.basename(song)
        shutil.copyfile(song, "./tracklist/" + os.path.basename(song))
        local_songs.append(new_song)

    # Keep songs list up-to-date
    songs = local_songs

    # Remove silence from songs (not yet implemented)
    for song in songs:
        ffmpeg.remove_silence(song, args.silence[0], args.silence[1])

    # Calculate the tracklist
    tracklist = Tracklist(songs)
    playlist_length = tracklist.time_in_sec

    # Combine all songs into one audio source
    ffmpeg.concat(songs, playlist_length)

    # Normalize files if they should be
    if (args.normalize):
        ffmpeg.normalize_audio(AUDIO_BITRATE, playlist_length)

    if (args.fit):
        thumbnail = utils.stretch_image(thumbnail)

    # Generate the mp4
    if (args.thumbnail != None):
        ffmpeg.generate_mp4(thumbnail, TITLE, AUDIO_BITRATE, VIDEO_BITRATE, playlist_length, output_fc)
    # Generate the mp3
    else:
        os.rename('big_audio.mp3', f'{TITLE}.mp3')
        output_fc.append(f'./{TITLE}.mp3')

    # Generate tracklist/captions if they should be
    if (args.data):
        tracklist.export_tracklist(songs, output_fc)

    # Move files to correct output folder
    for file in output_fc:
        shutil.move(file, os.path.join(args.output, file))

    utils.cleanup()

if __name__ == '__main__':
    main()