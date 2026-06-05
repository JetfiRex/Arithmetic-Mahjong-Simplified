import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from calculator_base.arithmetic_mahjong import ArithmeticMahjongChecker
from calculator_base.parser import parse_mode2_check_win


def hand(text):
    return parse_mode2_check_win(text)


@pytest.mark.parametrize(
    "text",
    [
        # 1+9=10, 2x3=6, 4刻子, 5对子
        "1 + 9 10 2 x 3 6 4 4 4 4 5 5",
        # 简单版没有“加法结果必须大于等于10”的限制：1+1=2 合法
        "1 + 1 2 3 x 4 12 5 5 5 5 6 6",
        # 一个已鸣牌组 + 两个手牌组 + 一对
        "(4 4 4 4) 1 + 1 2 3 x 4 12 6 6",
    ],
)
def test_arithmetic_can_win(text):
    checker = ArithmeticMahjongChecker()

    can_win, groups = checker.can_win(hand(text))

    assert can_win
    assert groups


@pytest.mark.parametrize(
    "text",
    [
        # 1+9 != 11
        "1 + 9 11 2 x 3 6 4 4 4 4 5 5",
        # 少一张，不能胡
        "1 + 9 10 2 x 3 6 4 4 4 4 5",
        # 对子不成立
        "1 + 9 10 2 x 3 6 4 4 4 4 5 6",
    ],
)
def test_arithmetic_cannot_win(text):
    checker = ArithmeticMahjongChecker()

    can_win, groups = checker.can_win(hand(text))

    assert not can_win
    assert groups == []


@pytest.mark.parametrize(
    "text",
    [
        "1 + 1 2",
        "1 + 9 10",
        "2 x 3 6",
        "6 x 2 3",
    ],
)
def test_formula_checker_accepts_valid_formula(text):
    checker = ArithmeticMahjongChecker()
    tiles = hand(f"{text} 4 4 4 4 5 5 6 6 6 6").hand_tiles[:4]

    assert checker.is_valid_formula(tiles)
