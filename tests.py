from path import path
from utils import rename
from nose.tools import eq_

def test_rename():
    """
    testing the renaming functionality
    """

    FOLDER = path("/tmp")
    expected = [
        ("Arrow.S01E20.HDTV.x264-LOL.mp4", "Arrow S01E20.mp4"),
        ("Techsnap-0106.mp4", "Techsnap-0106.mp4"),
        ("[HorribleSubs] Aku no Hana - 03 [720p].mkv", "Aku No Hana 03.mkv"),
        #anime with version numbers
        ("[HorribleSubs] Aku no Hana - 03v2 [720p].mkv", "Aku No Hana 03.mkv"),

        ("[HorribleSubs] Aku no Hana - 03 [720p].mkv", "Aku No Hana 03.mkv"),
        ("Fluent 2012_ Steve Souders, _Your Script Just Killed My Site_(720p_H.264-AAC).mp4",
         "Fluent 2012 - Steve Souders, Your Script Just Killed My Site.mp4"),
    ]

    for start, end in expected:
        out = rename(FOLDER.joinpath(start), dry_run=True)
        eq_(str(out.name), end)
