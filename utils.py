import os
import re
import shutil
import subprocess
from clint.textui import colored, puts
import guessit


BRACKET_RE = re.compile(r"\[.*?\]")
ANIME_RE = re.compile(r"%s.*(%s)+$" % (BRACKET_RE.pattern, BRACKET_RE.pattern))
YOUTUBE_RE = re.compile(r"\(.*?(aac|AAC)\)")
VIMEO_RE = re.compile(r"(?P<filename>.*?)(\d{3,})x(\d{3,}).*$")
MOVIE_RE = re.compile(r"(?P<movie>.*?)\.(?P<year>(19|20)\d\d)")


def notification(msg, show=True):
    """
    shows a notification for ubuntu
    """
    if show:
        os.system('notify-send "%s"' % msg)


def move_file(src, dest, dry_run=False):
    """
    performs the actual move of the file, with some helpful output, where
    fname and dest are paths
    """
    if dest.isdir():
        new_fname = dest.joinpath(src.name)
    else:
        new_fname = src

    print "%s => " % src.namebase,
    puts(colored.green(new_fname))
    if not dry_run:
        shutil.move(src, new_fname)


def smart_title(s):
    """
    titlecases a string, with some extra heuristics
    """
    out = []
    for w in s.split():
        if re.match(r"^[^A-Z]+$", w):
            out.append(w[0].upper() + w[1:])
        else:
            out.append(w)
    return " ".join(out)


def split_filter(arr, func):
    """
    uses the given function to filter the given array into matches and
    non-matches
    returns 2 lists of (matches, non-matches)
    """
    matches , non_matches = [], []
    for x in arr:
        if func(x):
            matches.append(x)
        else:
            non_matches.append(x)
    return matches , non_matches


def rename_anime(renamed):
    """
    renames an anime, given the namebase of a file
    """
    renamed = re.sub(BRACKET_RE, '', renamed).strip("_ ")
    #drop the version numbers if they exist
    renamed = re.sub(r"(\d+)[vV]\d+", r"\1", renamed)
    return renamed.replace("_", " ").replace(" - ", " ")


def rename_episode(renamed):
    """
    renames a tv episode, given the namebase of a file
    """
    info = guessit.guess_video_info("%s.avi" % (renamed))

    if info["type"] != "episode":
        return renamed

    #not a tv series, even though it might look like one
    series_exceptions = ["techsnap"]
    if info["series"].lower() in series_exceptions:
        return renamed

    #probably a youtube / vimeo video
    if "episodeNumber" not in info or "series" not in info:
        return renamed

    try:
        return "%(series)s S%(season)02dE%(episodeNumber)02d" % info
    except KeyError:
        return renamed


def rename(fp, dry_run=False):
    """
    renames the file / folder intelligently
    dry_run determines if the actual rename is performed
    """
    if not fp.isdir():
        #file extension
        ext = fp.ext.lower()
        #do not touch files that might be downloaded
        IGNORE_EXTS = (".rar", ".part", ".iso")
        if ext in IGNORE_EXTS:
            return

    name = fp.namebase
    renamed = name.strip().replace("!", '').strip("_ ").strip(".")

    #is it an anime?
    if ANIME_RE.search(renamed):
        renamed = rename_anime(renamed)
    else:
        renamed = rename_episode(renamed)

    #is it a youtube video?
    res = YOUTUBE_RE.search(renamed)
    if res:
        renamed = re.sub(YOUTUBE_RE, '', renamed).strip("_ ")
        renamed = re.sub(r"(\S)_\s", r"\1 - ", renamed)
        renamed = re.sub(r"\b_", '', renamed)

    #is it a vimeo video?
    res = VIMEO_RE.search(renamed)
    if res:
        renamed = res.groupdict()["filename"].strip("_")
        renamed = renamed.replace("_", " ")

    # #is it a movie downloaded from the web?
    # res = MOVIE_RE.search(renamed)
    # if res:
    #     renamed = res.groupdict()['movie']
    #     renamed = renamed.replace(".", " ")

    #title case!
    renamed = smart_title(renamed)

    # #super specific replacements
    # renamed = renamed.replace("Greys Anatomy", "Grey's Anatomy")
    # renamed = renamed.replace("Chihayafuru 2", "Chihayafuru S2")

    #print and rename output if unchanged
    if fp.isdir():
        target = fp.dirname().joinpath(renamed)
    else:
        target = fp.dirname().joinpath(renamed + ext)
    if renamed != name:
        print "%s => " % name,
        puts(colored.green(renamed))
        if not dry_run:
            fp.rename(target)
    print target
    return target


def run(cmd):
    """
    runs a command (array as accepted by subprocess)
    """
    subprocess.call(cmd, shell=False)


def command(cmd):
    """
    runs a command (array as accepted by subprocess) and returns its output as
    a list of lines
    """
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out, err = process.communicate()
    return out.splitlines()


def add_subtitles_mkv(video_file, sub_file, dry_run):
    """
    creates a new mkv file using the given video and subtitle file
    the name of the output is guessed from the video_file
    """
    if dry_run:
        return

    mkv_output = video_file.dirname().joinpath(video_file.namebase + ".mkv")
    puts(colored.green("Creating mkv: %s" % mkv_output))
    run(["mkvmerge", "-o", mkv_output, video_file, "--language", "0:en",
        "--track-name", "0:subtitle", "-s", "0", "-D", "-A", sub_file])

    video_file.remove()
    sub_file.remove()
