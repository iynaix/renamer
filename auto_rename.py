#! /usr/bin/env python

import guessit
from docopt import docopt
from path import path
from utils import notification, move_file, rename, add_subtitles_mkv

def HOME_DIR(*paths):
    return path("~/").expand().joinpath(*paths).abspath()


def smart_move_file(fname, video_dirs, dry_run=False):
    """
    attempts to copy the file for permanent storage if possible
    dry_run determines if the actual copy is performed
    """
    #see how good of a match we can get
    for v in video_dirs:
        #last element is the episode number
        if ' '.join(fname.namebase.split()[:-1]).startswith(v.name):
            move_file(fname, v)


def move_300mbunited(dry_run=False):
    """
    handle movies downloaded from 300mbunited, renaming them and moving them to
    the movies folder
    """
    for d in DOWNLOAD_DIR.dirs():
        if d.name.startswith("_FAILED"):
            continue

        #look for any movie directories
        if "300mbunited" in d.lower():
            #look for the mkvs
            for f in d.files():
                if f.endswith(".mkv"):
                    #move the file over
                    fp = rename(f, dry_run)
                    move_file(fp, HOME_DIR("Videos/Movies"), dry_run)
                    break
            #remove the directory
            if not dry_run:
                d.rmtree()


def move_tv_episodes(dry_run=False):
    """
    handle tv episodes downloaded by sabnzbd
    """
    episode_dirs = []
    for d in DOWNLOAD_DIR.dirs():
        if d.name.startswith("_FAILED"):
            continue

        #need to fake an extension
        info = guessit.guess_video_info(str(d)+".avi")
        if info["type"] != "episode":
            continue
        episode_dirs.append(d)

    for d in episode_dirs:
        #look for the largest file
        vid = sorted(d.files(), key=lambda f: f.size)[-1]

        info = guessit.guess_video_info(str(vid))
        fname = "%(series)s S%(season)02dE%(episodeNumber)02d" % info
        fp = vid.rename("%s%s" % (fname, vid.ext))
        move_file(fp, HOME_DIR("Videos/TO WATCH"), dry_run)

    for d in episode_dirs:
        #remove the directory
        if not dry_run:
            d.rmtree()


if __name__ == "__main__":
    doc = """Auto Renamer.

    Automatically renames and moves files to the external storage device if
    it is connected. Knows how to rename files from different sites such as
    youtube, vimeo, piratebay etc.

    Usage:
    rename.py [--debug] [--notify]
    rename.py (-h | --help)
    rename.py --version

    Options:
    -h --help     Show this screen.
    --version     Show version.
    --debug       Debug mode, no files are actually renamed.

    """
    args = docopt(doc, version='Auto Renamer 1.0 Beta')
    DEBUG = args["--debug"]
    show_notifications = args["--notify"]

    notification("Running RENAME script...", show_notifications)

    DOWNLOAD_DIR = HOME_DIR("Downloads")
    HDD_DIR = path("/media/iynaix/9b528a0a-22e7-410a-8bad-a4f52e97d407")

    #handle movies downloaded from 300mbunited.
    move_300mbunited()

    #handle tv episodes downloaded from 300mbunited.
    move_tv_episodes()

    #folders where the files will be renamed
    RENAME_DIRS = [
        HOME_DIR('Videos/WATCHED'),
        DOWNLOAD_DIR,
    ]

    MOVE_DIRS = [
        HOME_DIR('Videos/WATCHED'),
    ]

    #renaming files
    for d in RENAME_DIRS:
        with d:
            #do the renaming of files
            for f in d.files():
                rename(f, DEBUG)

            #check for subtitles and merge them if possible
            sub_files = [f for f in d.files() if f.ext in (".sub", ".srt")]
            for sub_file in sub_files:
                sub_name = sub_file.namebase
                #search for the corresponding video file
                for g in d.files():
                    if sub_name.startswith(g.namebase) and sub_file != g:
                        #add the subtitles file and remove the originals
                        add_subtitles_mkv(g, sub_file, DEBUG)
                        break

    #copy files if the storage is connected
    if HDD_DIR.exists():
        #try copying
        VIDEO_DIRS = HDD_DIR.joinpath("Anime").dirs()
        VIDEO_DIRS += HDD_DIR.joinpath("Videos").dirs()

        #copying files
        for d in MOVE_DIRS:
            for f in d.files():
                smart_move_file(f, VIDEO_DIRS, DEBUG)
