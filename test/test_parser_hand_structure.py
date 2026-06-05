import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from calculator_base.constants import ALL_TILES, MULTIPLY, PLUS, SYMBOLS, TILE_COUNTS
from calculator_base.hand_structure import Hand, MeldedGroup, Tile, create_tile_from_value
from calculator_base.parser import (
    parse_hand,
    parse_mode1_already_won,
    parse_mode2_check_win,
    parse_mode3_ready_with_meld,
    parse_mode4_ready_no_meld,
    validate_hand,
    validate_tile,
)


def test_simplified_tile_pool():
    assert SYMBOLS == {PLUS, MULTIPLY}
    assert len(ALL_TILES) == 24
    assert sum(TILE_COUNTS.values()) == 108
    assert "^" not in ALL_TILES
    assert 21 not in ALL_TILES


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 0),
        (20, 20),
        (24, 24),
        ("+", PLUS),
        ("×", MULTIPLY),
    ],
)
def test_tile_accepts_simplified_tiles(value, expected):
    assert Tile(value).value == expected


@pytest.mark.parametrize("value", [21, 25, "^", "joker_tiao"])
def test_tile_rejects_removed_complex_tiles(value):
    with pytest.raises(ValueError):
        Tile(value)


def test_create_tile_rejects_dora_and_joker_flags():
    with pytest.raises(ValueError):
        create_tile_from_value(11, is_dora=True)

    with pytest.raises(ValueError):
        create_tile_from_value(11, is_joker_used=True)


def test_melded_group_accepts_simplified_group_types():
    pong = MeldedGroup([Tile(4), Tile(4), Tile(4), Tile(4)], "碰")
    assert pong.group_type == "碰"
    assert pong.tile_count() == 4

    kong = MeldedGroup([Tile(4), Tile(4), Tile(4), Tile(4), Tile(4)], "明杠")
    assert kong.group_type == "明杠"
    assert kong.tile_count() == 5
    assert kong.group_count_value() == 4


@pytest.mark.parametrize(
    ("tiles", "group_type"),
    [
        ([Tile(4)], "单张杠"),
        ([Tile(4), Tile(4), Tile(4), Tile(4)], "明杠"),
        ([Tile(4), Tile(4), Tile(4), Tile(4), Tile(4)], "碰"),
    ],
)
def test_melded_group_rejects_invalid_group_types_or_counts(tiles, group_type):
    with pytest.raises(ValueError):
        MeldedGroup(tiles, group_type)


def test_hand_counts_exclude_extra_kong_tile_from_logical_total():
    kong = MeldedGroup([Tile(4), Tile(4), Tile(4), Tile(4), Tile(4)], "明杠")
    hand = Hand(melded_groups=[kong], hand_tiles=[Tile(1), Tile(PLUS), Tile(9), Tile(10)])

    assert hand.total_tile_count() == 8
    assert hand.actual_tile_count() == 9
    assert hand.get_all_tiles_simple() == [4, 4, 4, 4, 4, 1, PLUS, 9, 10]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1 + 9 10", [1, PLUS, 9, 10]),
        ("2 x 3 6", [2, MULTIPLY, 3, 6]),
        ("2 X 3 6", [2, MULTIPLY, 3, 6]),
        ("2 * 3 6", [2, MULTIPLY, 3, 6]),
        ("2 × 3 6", [2, MULTIPLY, 3, 6]),
        ("1,+,9,10", [1, PLUS, 9, 10]),
    ],
)
def test_parse_hand_accepts_simplified_input(text, expected):
    assert parse_hand(text) == expected


@pytest.mark.parametrize("text", ["^", "11d", "5w", "21", "25", "joker_tiao"])
def test_parse_hand_rejects_complex_or_illegal_input(text):
    with pytest.raises(ValueError):
        parse_hand(text)


def test_validate_tile_and_validate_hand():
    assert validate_tile(24)
    assert validate_tile(PLUS)
    assert not validate_tile(21)
    assert not validate_tile("^")

    assert validate_hand([1, PLUS, 9, 10]) == (True, "")
    assert not validate_hand([1, PLUS, 21, 10])[0]
    assert not validate_hand([1, PLUS, 9, 10], expected_len=13)[0]


def test_parse_mode1_grouped_winning_hand():
    hand = parse_mode1_already_won(
        "1 + 9 [10] / 2 x 3 6 / 4 4 4 4 / 5 5 {zimo}"
    )

    assert hand.win_type == "算术麻将"
    assert hand.winning_tile.value == 10
    assert hand.winning_tile.winning
    assert hand.winning_method == "自摸"
    assert [len(group) for group in hand.hand_groups] == [4, 4, 4, 2]
    assert hand.total_tile_count() == 14


def test_parse_mode2_ungrouped_winning_hand_with_meld():
    hand = parse_mode2_check_win("(4 4 4 4) 1 + 9 [10] 2 x 3 6 5 5")

    assert len(hand.melded_groups) == 1
    assert hand.melded_groups[0].group_type == "碰"
    assert hand.winning_tile.value == 10
    assert [tile.value for tile in hand.hand_tiles] == [
        1,
        PLUS,
        9,
        10,
        2,
        MULTIPLY,
        3,
        6,
        5,
        5,
    ]
    assert hand.total_tile_count() == 14


def test_parse_mode3_ready_hand_with_meld():
    hand = parse_mode3_ready_with_meld("(4 4 4 4) 1 + 9 10 2 x 3 6 5")

    assert hand.should_win_in_mode is False
    assert len(hand.melded_groups) == 1
    assert hand.melded_groups[0].group_type == "碰"
    assert [tile.value for tile in hand.hand_tiles] == [1, PLUS, 9, 10, 2, MULTIPLY, 3, 6, 5]
    assert hand.total_tile_count() == 13


def test_parse_mode4_ready_hand_without_meld():
    hand = parse_mode4_ready_no_meld("1 + 9 10 2 x 3 6 4 4 4 4 5")

    assert hand.should_win_in_mode is False
    assert hand.melded_groups == []
    assert len(hand.hand_tiles) == 13
    assert hand.total_tile_count() == 13
