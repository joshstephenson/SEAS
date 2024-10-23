import pytest
from src.subtitles import Subtitles
from src.helpers import get_text


@pytest.fixture
def subs():
    text = get_text('test_data/has_brackets.srt')
    return Subtitles(text)

def test_removes_eight_subtitles(subs):
    assert len([*subs]) == 6

def test_has_no_brackets(subs):
    for sub in subs:
        assert '{\an8}' not in sub.text
        assert '[in Mandarin] ' not in sub.text
        assert '[' not in sub.text
        assert ']' not in sub.text