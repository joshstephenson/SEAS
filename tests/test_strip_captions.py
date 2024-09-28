import pytest
from subtitles import Subtitles
from subtitle import Subtitle
from align import get_text
import re

@pytest.fixture
def captions():
    text = get_text('test_data/captions.srt')
    return Subtitles(text)


def test_3_subtitles_get_stripped(captions):
    assert len([*captions]) == 9

# We want to strip strings of all uppercase when that string has more than one word in uppercase
def test_multiple_words_in_all_captions_with_optional_punctuation_are_stripped(captions):
    # assert captions.subtitles[0].text == 'we zijn er bijna. Word maar wakker.'
    text = captions.subtitles[0].text

    for sub in captions.subtitles:
        assert re.search('HUUR ME IN, MR CHOCOLATE', sub.text) is None
        assert re.search('SHANIA REED IS DE VOLGENDE STER', sub.text) is None
        assert re.search('STUDIO CHOCOLATE', sub.text) is None

def test_that_single_words_in_all_caps_are_not_stripped_unless_they_are_at_beginning_with_subsequent_colon(captions):
    text = captions.subtitles[8].text
    assert re.search('IRS', text) is not None
    assert re.search('FBI', text) is not None
    assert re.search('AFAIK', text) is not None

    text = captions.subtitles[0].text
    assert re.search('LOTTIE:', text) is None

    text = captions.subtitles[1].text
    assert re.search(r'Person #2:*', text) is None
    assert captions.subtitles[1].text == 'Blah blah blah.'
