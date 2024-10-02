import pytest
from subtitles import Subtitles
from subtitle import Subtitle
from align import get_text
import re

@pytest.fixture
def subs():
    text = get_text('test_data/quoted.srt')
    return Subtitles(text)

def test_removes_entire_subs_if_everything_is_quoted(subs):
    assert len([*subs]) == 3

def test_strips_all_types_of_quoted_content(subs):
    for sub in subs:
        assert '"' not in sub.text
        for char in '"“”«»„‟‹›〝〞『』【】「」':
            assert char not in sub.text
    text = subs.subtitles[2].text
    assert text == "editor really had no idea."