import pytest
from subtitles import Subtitles
from scripts.align import get_text


@pytest.fixture
def subs():
    text = get_text('test_data/urls.srt')
    return Subtitles(text)

def test_strips_urls(subs):
    assert len([*subs]) == 0