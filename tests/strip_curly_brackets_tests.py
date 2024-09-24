import pytest
from subtitles import Subtitles
from subtitle import Subtitle
from align import get_text
import re

@pytest.fixture
def brackets():
    text = get_text('test_data/has_curly_brackets.srt')
    return Subtitles(text, sterilize=True)

def test_has_no_brackets(brackets):
    for bracket in brackets:
        assert '{\an8}' not in bracket.text