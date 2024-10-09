import pytest
from subtitles import Subtitles
from helpers import get_text


@pytest.fixture
def captions_en():
    text = get_text('test_data/multi_speaker_en.srt')
    return Subtitles(text)

@pytest.fixture
def captions_es():
    text = get_text('test_data/multi_speaker_es.srt')
    return Subtitles(text)

def test_splits_single_subtitle_with_multiple_speakers_into_two(captions_en, captions_es):
    assert len([*captions_en.subtitles]) == 3 # English has a test to make sure we don't split a hypen in the middle of the sentence
    assert len([*captions_es.subtitles]) == 2

