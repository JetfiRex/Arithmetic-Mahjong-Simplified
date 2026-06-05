import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from calculator_base.mahjong_checker import ArithmeticMahjong
from calculator_base.parser import parse_mode1_already_won, parse_mode2_check_win
from fan_calculator.fan_base import FanType
from fan_calculator.fan_calculator import FanCalculator


def fan_types(result):
    return {fan.fan_type for fan in result.results}


def grouped_hand(text):
    return parse_mode1_already_won(text)


def ungrouped_hand(text):
    return parse_mode2_check_win(text)


def test_quan_duo_bei_excludes_lower_multiple_fans():
    hand = grouped_hand("6 6 6 6 / 12 12 12 12 / 18 18 18 18 / 6 6")
    result = FanCalculator().calculate(hand)
    types = fan_types(result)

    assert FanType.QUAN_DUO_BEI in types
    assert FanType.QUAN_SAN_BEI not in types
    assert FanType.QUAN_OU_SHU not in types


def test_quan_duo_bei_applies_to_hand_without_number_tiles():
    hand = grouped_hand("+ + + + / × × × × / + + + + / × ×")
    result = FanCalculator().calculate(hand)

    assert FanType.QUAN_DUO_BEI in fan_types(result)


def test_san_men_qi_requires_kezi_plus_formula_and_multiply_formula():
    hand = grouped_hand("1 + 9 10 / 2 x 3 6 / 4 4 4 4 / 5 5")
    result = FanCalculator().calculate(hand)

    assert FanType.SAN_MEN_QI in fan_types(result)


def test_no_fan_shape_does_not_satisfy_starting_fan():
    hand = grouped_hand("1 + 9 10 / 2 x 3 6 / 5 + 7 12 / 14 14")
    calculator = FanCalculator(min_fan=1)
    result = calculator.calculate(hand)

    assert result.get_total_fan() == 0
    assert not calculator.can_win(hand)


def test_top_level_checker_warns_but_keeps_no_fan_shape_win():
    hand = ungrouped_hand("1 + 9 10 2 x 3 6 5 + 7 12 14 14")
    checker = ArithmeticMahjong()

    can_win, groups, win_type, fan_info = checker.can_win(hand)

    assert can_win
    assert groups
    assert win_type == "算术麻将"
    assert fan_info["total_fan"] == 0
    assert not fan_info["can_start"]
    assert "警告" in checker.format_result(can_win, groups, win_type, fan_info)


def test_top_level_checker_can_still_shape_check_with_min_fan_zero():
    hand = ungrouped_hand("1 + 9 10 2 x 3 6 5 + 7 12 14 14")
    checker = ArithmeticMahjong(min_fan=0)

    can_win, groups, win_type, fan_info = checker.can_win(hand)

    assert can_win
    assert groups
    assert win_type == "算术麻将"
    assert fan_info["total_fan"] == 0
