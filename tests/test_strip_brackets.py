import pytest
from subtitles import Subtitles
from subtitle import Subtitle
from align import get_text
import re

@pytest.fixture
def subs():
    text = get_text('test_data/has_brackets.srt')
    return Subtitles(text, sterilize=True)

def test_removes_eight_subtitles(subs):
    assert len([*subs]) == 8

def test_has_no_brackets(subs):
    for sub in subs:
        assert '{\an8}' not in sub.text
        assert '[in Mandarin] ' not in sub.text