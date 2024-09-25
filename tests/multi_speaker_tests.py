import pytest
from subtitles import Subtitles
from subtitle import Subtitle
from align import get_text
import re

@pytest.fixture
def captions():
    text = get_text('test_data/multi_speaker.srt')
    return Subtitles(text)
