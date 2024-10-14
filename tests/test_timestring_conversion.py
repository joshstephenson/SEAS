from src.helpers import parse_timestring, microseconds_to_string


def test_timestring_conversion():
    timestring = '00:56:18,334'
    assert parse_timestring(timestring) == 3378334000
    assert microseconds_to_string(parse_timestring(timestring)) == timestring