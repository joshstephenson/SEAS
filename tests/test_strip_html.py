import pytest
from subtitles import Subtitles
from subtitle import Subtitle
from align import get_text
import re

@pytest.fixture
def subs():
    text = get_text('test_data/html.srt')
    return Subtitles(text, sterilize=True)

def test_removes_entire_subs_when_html_wraps_all_text(subs):
    assert len([*subs]) == 2

def test_strips_html(subs):
    for sub in subs:
        assert '<i>Pese a todos nuestros altibajos</i>' not in sub.text
        assert '<i>' not in sub.text
        assert '</i>' not in sub.text