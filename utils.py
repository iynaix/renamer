import os
import re
import shutil
import subprocess
from clint.textui import colored, puts


BRACKET_RE = re.compile(r"\[.*?\]")
ANIME_RE = re.compile(r"%s.*(%s)+$" % (BRACKET_RE.pattern, BRACKET_RE.pattern))
YOUTUBE_RE = re.compile(r"\(.*?(aac|AAC)\)")
TV_RE = re.compile(r"\.(hdtv|HDTV|pdtv|PDTV).*")
MOVIE_RE = re.compile(r"(?P<movie>.*?)\.(?P<year>(19|20)\d\d)")
VIMEO_RE = re.compile(r"(?P<filename>.*?)(\d{3,})x(\d{3,}).*$")


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


def rename(fp, dry_run=False):
    """
    renames the file intelligently
    dry_run determines if the actual rename is performed
    """

    #file extension
    ext = fp.ext.lower()
    #do not touch files that might be downloaded
    if ext == ".rar" or ext == ".part":
        return

    name = fp.namebase
    renamed = name.strip()
    renamed = renamed.replace("!", '').strip("_ ").strip(".")

    #is it an anime?
    res = ANIME_RE.search(renamed)
    if res:
        renamed = re.sub(BRACKET_RE, '', renamed).strip("_ ")
        renamed = renamed.replace("_", " ").replace(" - ", " ")

    #is it a youtube video?
    res = YOUTUBE_RE.search(renamed)
    if res:
        renamed = re.sub(YOUTUBE_RE, '', renamed).strip("_ ")
        renamed = re.sub(r"(\S)_\s", r"\1 - ", renamed)

    #is it a viemo video?
    res = VIMEO_RE.search(renamed)
    if res:
        renamed = res.groupdict()["filename"].strip("_")
        renamed = renamed.replace("_", " ")

    #is it a movie downloaded from the web?
    res = MOVIE_RE.search(renamed)
    if res:
        renamed = res.groupdict()['movie']
        renamed = renamed.replace(".", " ")

    #is it a tv series download from the web?
    res = TV_RE.search(renamed)
    if res:
        renamed = re.sub(TV_RE, '', renamed).strip("_ ")
        renamed = renamed.replace(".", " ")
        tmp = renamed.split()
        renamed = ' '.join(x.title() for x in tmp[:-1])

        #handle the episodes
        episode = tmp[-1].upper()
        if not re.match(r"^S\d+E\d+$", episode):
            if re.match(r"^\d+$", episode):
                episode = "S%02dE%02d" % (int(episode[:-2]), int(episode[-2:]))
        renamed = '%s %s' % (renamed, episode)

    #title case!
    renamed = smart_title(renamed)

    #super specific replacements
    renamed = renamed.replace("Greys Anatomy", "Grey's Anatomy")
    renamed = renamed.replace("Chihayafuru 2", "Chihayafuru S2")

    #print and rename output if unchanged
    if renamed != name:
        print "%s => " % name,
        puts(colored.green(renamed))
        target = fp.dirname().joinpath(renamed + ext)
        if not dry_run:
            fp.rename(target)
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
