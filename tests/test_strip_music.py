import pytest
from subtitles import Subtitles
from scripts.align import get_text


@pytest.fixture
def subs():
    text = get_text('test_data/music_notes.srt')
    return Subtitles(text)

def test_removes_four_of_six_subtitles(subs):
    assert len([*subs]) == 2

def test_removes_subtitles_containing_musical_notes(subs):
    for sub in subs:
        assert '♪' not in sub.text
        assert '#' not in sub.text