#! /usr/bin/env python

from docopt import docopt
from path import path
from collections import Counter

import guessit
from clint.textui import colored, puts
from utils import move_file, rename

def HOME_DIR(*paths):
    return path("~/").expand().joinpath(*paths).abspath()


def guess_folder(d):
    """
    guess the type of folder given a path to the folder
    """
    MUSIC_EXTS = ("mp3", "flac", "ape", "wav")
    VIDEO_EXTS = ("avi", "mp4", "mkv", "m4v")

    #get the types of the files
    ftypes = {}
    for f in d.walkfiles():
        ext = f.ext.lower()[1:]
        if ext in MUSIC_EXTS:
            ftypes[f] = "music"
            continue
        elif ext in VIDEO_EXTS:
            ftypes[f] = "video"
            continue
        # else:
        #     ftypes[f] = "unknown"
        #     continue

    ftype_counts = Counter(ftypes.values()).most_common()
    try:
        return ftype_counts[0][0]
    except:
        return "unknown"


def rename_video(f, dry_run=True):
    """
    rename a video file using guessit info
    """
    info = guessit.guess_video_info(str(f))
    if info["type"] == "movie":
        fp = f.rename("%s%s" % (info["title"], f.ext))
        move_file(fp, HOME_DIR("Videos/Movies"), dry_run)
    elif info["type"] == "episode":
        fname = "%(series)s S%(season)02dE%(episodeNumber)02d" % info
        fp = f.rename("%s%s" % (fname, f.ext))
        move_file(fp, HOME_DIR("Videos/TO WATCH"), dry_run)


def handle_video_dir(d, dry_run=True):
    file_sizes = [f.size for f in d.walkfiles()]
    total_size = sum(file_sizes) * 1.0
    size_ratios = sorted([s / total_size for s in file_sizes], reverse=True)

    if size_ratios[0] >= 0.95:
        vid = sorted(d.walkfiles(), key=lambda f: f.size)[-1]

        info = guessit.guess_video_info(str(vid))
        if info["type"] == "movie":
            fp = vid.rename("%s%s" % (info["title"], vid.ext))
            move_file(fp, HOME_DIR("Videos/Movies"), dry_run)
        elif info["type"] == "episode":
            fname = "%(series)s S%(season)02dE%(episodeNumber)02d" % info
            fp = vid.rename("%s%s" % (fname, vid.ext))
            move_file(fp, HOME_DIR("Videos/TO WATCH"), dry_run)

        #remove the directory
        if not dry_run:
            d.rmtree()
    else:
        #multiple video files, rename them
        for f in d.files():
            rename(f, dry_run)
        #move the directory
        if not dry_run:
            fp = rename(d, dry_run)
            fp.move(HOME_DIR("Videos/TO WATCH"))


if __name__ == "__main__":
    doc = """Guess Folders 0.1.

    Guesses and organises the folders within the given directories
    Automatically renames and moves files to the external storage device if
    it is connected. Knows how to rename files from different sites such as
    youtube, vimeo, piratebay etc.

    Usage:
    guess_folders.py [--debug] [<directories>...]
    guess_folders.py (-h | --help)
    guess_folders.py --version

    Options:
    -h --help     Show this screen.
    --version     Show version.
    --debug       Debug mode, no files are actually renamed.
    """

    args = docopt(doc, version='Guess Folders 0.1')
    DEBUG = args["--debug"]

    folders = [path(d) for d in args["<directories>"]]
    if not args["<directories>"]:
        folders = [HOME_DIR("Downloads/pending")]

    for folder in folders:
        with folder:
            for d in folder.dirs():
                if guess_folder(d) == "video":
                    puts(colored.green(d.name))
                    handle_video_dir(d, DEBUG)
