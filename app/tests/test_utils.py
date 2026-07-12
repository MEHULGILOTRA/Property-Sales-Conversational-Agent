from app.agent.utils import parse_budget


def test_full_number():
    assert parse_budget("my budget is 800000 usd") == 800000


def test_thousands_shorthand():
    assert parse_budget("around 600k") == 600000


def test_millions_shorthand():
    assert parse_budget("up to 1.2 million") == 1200000
    assert parse_budget("2 mn budget") == 2000000


def test_full_number_wins_over_shorthand():
    assert parse_budget("400000, not 800k") == 400000


def test_bare_m_is_not_a_budget():
    # "350m" usually means square meters, not 350 million dollars
    assert parse_budget("3bhk phuket 350m") is None


def test_bhk_is_not_a_budget():
    assert parse_budget("show me a 3 bhk") is None


def test_empty():
    assert parse_budget("") is None
