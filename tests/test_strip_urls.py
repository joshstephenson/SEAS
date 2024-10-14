import pytest
from src.subtitles import Subtitles
from src.helpers import get_text


@pytest.fixture
def subs():
    text = get_text('test_data/urls.srt')
    return Subtitles(text)

def test_strips_urls(subs):
    assert len([*subs]) == 0