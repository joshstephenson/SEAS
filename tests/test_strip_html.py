import pytest
from subtitles import Subtitles
from subtitle import Subtitle
from align import get_text
import re

@pytest.fixture
def subs():
    text = get_text('test_data/html.srt')
    return Subtitles(text)

@pytest.fixture
def three_body_subs():
    text = get_text('test_data/3_body_problem-countdown-spa.srt')
    return Subtitles(text)

def test_removes_entire_subs_when_html_wraps_all_text(subs):
    for sub in subs:
        print(sub.text)
    assert len([*subs]) == 6

def test_strips_html(subs):
    for sub in subs:
        assert 'Pese a todos nuestros altibajos' not in sub.text
        assert re.match(r'<.+>', sub.text) is None

def test_strips_html_from_3_body_problem_spa(three_body_subs):
    for sub in three_body_subs:
        assert re.match(r'<.+>', sub.text) is None