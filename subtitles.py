"""
Searches and lists the movies that do not contain subtitles.
"""

import subprocess
from path import path
from utils import split_filter
import subliminal
import guessit
from utils import command


def remove_subtitles(mkv):
    """
    uses mkvmerge to remove the subtitles from the given file
    """
    print "REMOVING SUBTITLES: %s" % mkv

    out_file = path("/tmp/out.mkv")
    run(["mkvmerge", "-o", out_file, "--no-subtitles", mkv])
    #replace the original
    out_file.copy(mkv)


def has_subtitles(mkv_file):
    """
    does the mkv file have subtitles?
    """
    info = command(["mkvinfo", mkv_file])

    sub_lines = []
    for line_no, line in enumerate(info):
        if "Track type" in line and "subtitles" in line:
            sub_lines.append(line_no)

    if not sub_lines:
        return False

    track_nos = []
    for sub_line in sub_lines:
        for line in info[sub_line:0:-1]:
            if "Track number" in line:
                track_nos.append(int(line.split(":").pop().strip()))
                break

    #extract the subtitle to a file
    sub_sizes = []
    for track_no in track_nos:
        sub_out = "/tmp/subs.srt"
        run(["mkvextract", "tracks",  mkv_file, "%s:%s" % (track_no, sub_out)])
        sub_sizes.append(path(sub_out).size)
    for sub_size in sub_sizes:
        #subtitle is too short, it's just the one liner
        if sub_size < 500:
            #remove the subtitle since they're meaningless
            remove_subtitles(mkv_file)
            return False
    return True


def is_valid_subtitle(sub):
    """
    returns True if the subtitle is valid, False otherwise
    """
    info = guessit.guess_video_info(sub.release)
    if info["type"] != "moviesubtitle":
        return False
    if info["container"] != "srt":
        return False

    #filter out those that are not english
    if "language" in info:
        if "english" not in repr(info["language"]).lower():
            return False
    if "subtitleLanguage" in info:
        if "english" not in repr(info["subtitleLanguage"]).lower():
            return False

    #uninterested in split srt files
    if "cdNumber" in info:
        return False

    return True


def get_subtitles(fname):
    """
    returns a list of subtitles given a path
    """
    #search using info from the actual file
    subs = subliminal.list_subtitles(str(fname), ["en"], force=True,
                                     cache_dir="/tmp/")
    subs = subs.values()[0]
    #remove everything that is not a movie
    subs = filter(is_valid_subtitle, subs)
    if subs:
        return subs

    subs = subliminal.list_subtitles(str(fname.name), ["en"], force=True,
                                     cache_dir="/tmp/")
    subs = subs.values()[0]
    #remove everything that is not a movie
    subs = filter(is_valid_subtitle, subs)
    return subs


def download_subtitle(sub, video):
    """
    downloads the given subtitle for the given video
    """
    task = subliminal.tasks.DownloadTask(video, [sub])
    #start the actual download
    subliminal.core.consume_task(task)


if __name__ == "__main__":
    MOVIE_DIR = path("~/Videos/Movies").expand()

    #final list of videos with no subtitles
    no_subs = []

    all_files = sorted(MOVIE_DIR.files())
    subtitles, videos = split_filter(all_files,
                                        lambda x: x.ext in (".srt", ".sub"))

    #eliminate the videos that have external subs
    for sub in subtitles:
        sub_name = sub.namebase
        for vid in videos:
            #rename the subtitle file to match the video
            if sub_name.startswith(vid.namebase):
                new_sub_fname = "%s%s" % (vid.namebase, sub.ext)
                sub.rename(MOVIE_DIR / new_sub_fname)
                break
        videos.remove(vid)

    mkvs, non_mkvs = split_filter(videos, lambda x: x.ext == ".mkv")
    no_subs += non_mkvs

    for mkv in mkvs:
        if not has_subtitles(mkv):
            no_subs.append(mkv)

    for video in no_subs:
        subs = get_subtitles(video)
        subs = sorted(subs, key=lambda x: x.confidence, reverse=True)
        if subs:
            print "Downloading subtitle:", video.namebase
            download_subtitle(subs[0], video)
