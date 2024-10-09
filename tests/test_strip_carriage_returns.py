import pytest
from subtitles import Subtitles
from helpers import get_text
import re

@pytest.fixture
def subs():
    text = get_text('test_data/carriage_returns.srt')
    return Subtitles(text)

def test_strip_carriage_returns(subs):
    assert len([*subs]) == 1
    for sub in subs:
        assert re.search(r'\r', sub.text) is None