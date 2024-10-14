import pytest

from src.annotation import Annotation
from src.subtitles import Subtitles
from src.helpers import get_text


@pytest.fixture
def annotation1():
    en_text = """6
00:00:25,150 --> 00:00:26,484
[crying] I beg you

7
00:00:26,568 --> 00:00:29,696
to rehabilitate me!
"""
    es_text = """5
00:00:25,109 --> 00:00:26,327
Se lo ruego.

6
00:00:26,527 --> 00:00:28,738
Rehabilítenme.
"""
    en_subtitles = Subtitles(en_text).subtitles
    es_subtitles = Subtitles(es_text).subtitles

    annotation = Annotation(en_subtitles,
                            es_subtitles,
                            "I beg you to rehabilitate me!",
                            "Se lo ruego. Rehabilítenme.")
    return annotation

@pytest.fixture
def annotation2():
    en_text = """3
00:00:14,889 --> 00:00:17,475
<i>Sweep away all monsters and demons!</i>
"""
    es_text = """3
00:00:14,849 --> 00:00:17,935
¡Fuera los monstruos y demonios!
"""
    en_subtitles = Subtitles(en_text).subtitles
    es_subtitles = Subtitles(es_text).subtitles

    annotation = Annotation(en_subtitles,
                            es_subtitles,
                            "Sweep away all monsters and demons!",
                            "¡Fuera los monstruos y demonios!")
    return annotation

def test_highlighting_multiple(annotation1):
    subtitle1 = annotation1.source.subtitles[0]
    subtitle2 = annotation1.source.subtitles[1]
    x1 = len("""6
00:00:25,150 --> 00:00:26,484
[crying] """)

    x2 = len("""7
00:00:26,568 --> 00:00:29,696
""")
    assert annotation1.source.get_offsets_and_length(subtitle1) == (2, x1, len("I beg you"))
    assert annotation1.source.get_offsets_and_length(subtitle2) == (2, x2, len("to rehabilitate me."))

def test_highlighting_simple(annotation2):
    subtitle1 = annotation2.source.subtitles[0]
    x = len("""3
00:00:14,889 --> 00:00:17,475
<i>""")
    assert annotation2.source.get_offsets_and_length(subtitle1) == (2, x, 35)
