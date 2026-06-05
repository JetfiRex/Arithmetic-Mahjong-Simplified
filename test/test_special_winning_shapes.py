import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from calculator_base.special_winning_checker import SpecialWinningChecker
from calculator_base.traditional_mahjong import TraditionalMahjongChecker
from calculator_base.parser import parse_mode2_check_win


def values(text):
    return [tile.value for tile in parse_mode2_check_win(text).hand_tiles]


@pytest.mark.parametrize(
    "text",
    [
        "1 2 3 4 5 6 10 10 11 12 13 + + +",
        "1 1 1 4 5 6 11 12 13 20 20 20 + +",
    ],
)
def test_traditional_mahjong_can_win(text):
    checker = TraditionalMahjongChecker()

    can_win, groups = checker.can_win_traditional(values(text))

    assert can_win
    assert groups


@pytest.mark.parametrize(
    "text",
    [
        "1 1 2 2 3 3 4 4 5 5 6 6 7 7",
        "0 0 2 2 4 4 6 6 8 8 10 10 + +",
    ],
)
def test_seven_pairs_can_win(text):
    checker = SpecialWinningChecker()

    can_win, groups = checker.can_win_qi_xiao_dui(values(text))

    assert can_win
    assert len(groups) == 7


@pytest.mark.parametrize(
    "text",
    [
        "1 1 2 2 3 3 4 4 5 5 6 6 7 7",
        "2 2 4 4 6 6 8 8 10 10 12 12 14 14",
    ],
)
def test_linked_seven_pairs_can_win(text):
    checker = SpecialWinningChecker()

    can_win, groups = checker.can_win_lian_qi_dui(values(text))

    assert can_win
    assert len(groups) == 7


@pytest.mark.parametrize(
    "text",
    [
        "1 2 3 4 5 6 7 8 9 10 11 12 16 16",
        "5 6 7 8 9 10 11 12 13 14 15 16 + +",
    ],
)
def test_qing_long_can_win(text):
    checker = SpecialWinningChecker()

    can_win, groups = checker.can_win_qing_long(values(text))

    assert can_win
    assert groups


@pytest.mark.parametrize(
    "text",
    [
        "1 1 2 2 3 3 4 4 5 5 6 6 8 8",
        "1 2 3 4 5 6 7 8 9 10 11 13 16 16",
    ],
)
def test_special_shape_rejects_invalid_examples(text):
    checker = SpecialWinningChecker()
    hand_values = values(text)

    assert not checker.can_win_lian_qi_dui(hand_values)[0]
    assert not checker.can_win_qing_long(hand_values)[0]
