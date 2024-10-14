import pytest
from src.helpers import get_text, collate_subs, print_partition
from src.film import find_partitions
from src.subtitles import Subtitles


@pytest.fixture
def subs_en():
    en_text = get_text('test_data/partition_en.srt')
    return Subtitles(en_text)


@pytest.fixture
def subs_es():
    es_text = get_text('test_data/partition_es.srt')
    return Subtitles(es_text, False)


def test_partioning_splits(subs_en, subs_es):
    collated = collate_subs(subs_en.subtitles, subs_es.subtitles)
    partitions = find_partitions(collated)
    assert len(partitions) == 4

    first_partition = partitions[0]
    assert len(first_partition.source.subtitles) == 1
    assert len(first_partition.source.utterances) == 0
    assert len(first_partition.target.subtitles) == 0
    assert len(first_partition.target.utterances) == 0

    second_partition = partitions[1]
    assert len(second_partition.source.subtitles) == 1
    assert len(second_partition.source.utterances) == 0
    assert len(second_partition.target.subtitles) == 0
    assert len(second_partition.target.utterances) == 0

    third_partition = partitions[2]
    assert len(third_partition.source.subtitles) == 1
    assert len(third_partition.source.utterances) == 2
    assert len(third_partition.target.subtitles) == 1
    assert len(third_partition.target.utterances) == 2

    fourth_partition = partitions[3]
    assert len(fourth_partition.source.subtitles) == 1
    assert len(fourth_partition.source.subtitles) == 1


@pytest.fixture
def subs2_en():
    en_text = get_text('test_data/partition2_en.srt')
    return Subtitles(en_text)


@pytest.fixture
def subs2_es():
    es_text = get_text('test_data/partition2_es.srt')
    return Subtitles(es_text, False)


def test_partitioning_unions(subs2_en, subs2_es):
    collated = collate_subs(subs2_en.subtitles, subs2_es.subtitles)
    partitions = find_partitions(collated)

    assert len(partitions) == 1, [str(p) for p in partitions]
