import pytest

from src.helpers import find_utterances
from src.subtitle import Subtitle
from src.utterance import Utterance

@pytest.fixture
def subtitles():
    return [Subtitle('756\n00:45:32,000 --> 00:45:34,000\nIt will look like a...'),
            Subtitle('757\n00:45:34,000 --> 00:45:37,000\nheart attack or car accident.'),
            Subtitle('758\n00:45:38,000 --> 00:45:40,000\nHere is a list of one, '),
            Subtitle('759\n00:45:41,000 --> 00:45:42,000\ntwo,'),
            Subtitle('759\n00:45:41,000 --> 00:45:42,000\nthree.')]

@pytest.fixture
def starts_utterance():
    sub = Subtitle('756\n00:45:32,056 --> 00:45:34,365\nIt will look like a...')
    return [Utterance('It will look like a...', [sub])]

@pytest.fixture()
def ends_utterance():
    sub = Subtitle('757\n00:45:34,389 --> 00:45:37,623\nheart attack or car accident.')
    return [Utterance('heart attack or a car accident.', [sub])]

def test_starts_utterance(starts_utterance):
    for utterance in starts_utterance:
        assert utterance.starts_utterance() is True
        assert utterance.ends_utterance() is False

def test_ends_utterance(ends_utterance):
    for utterance in ends_utterance:
        assert utterance.starts_utterance() is False
        assert utterance.ends_utterance() is True

def test_find_utterances(subtitles):
    utterances = find_utterances(subtitles)
    assert len(utterances) == 2
