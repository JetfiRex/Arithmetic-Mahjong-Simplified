import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from calculator_base.mahjong_checker import ArithmeticMahjong
from calculator_base.parser import parse_mode3_ready_with_meld, parse_mode4_ready_no_meld
from fan_calculator.fan_base import FanType


def ready_hand(text):
    return parse_mode4_ready_no_meld(text)


def ready_hand_with_meld(text):
    return parse_mode3_ready_with_meld(text)


def make_checker():
    # These tests only check whether a hand is ready. Fan/start requirements are
    # deliberately disabled in tests with min_fan=0.
    return ArithmeticMahjong(min_fan=0)


def test_ready_for_multiple_arithmetic_tiles():
    checker = make_checker()
    hand = ready_hand("1 + 9 10 2 x 3 6 4 4 4 4 5")

    is_ready, ready_info = checker.is_ready(hand)

    assert is_ready
    assert "算术麻将" in ready_info
    assert set(ready_info["算术麻将"]) == {"1", "5", "×"}


def test_not_ready_hand_returns_false():
    checker = make_checker()
    hand = ready_hand("1 + 9 10 2 x 3 6 4 4 4 5 6")

    is_ready, ready_info = checker.is_ready(hand)

    assert not is_ready
    assert ready_info == {}


def test_ready_tile_can_be_empty_listening():
    checker = make_checker()
    # Adding 0 completes:
    # 0+1=1 / 0x5=0 / 2x3=6 / 0,0
    # But the hand already uses all four 0 tiles, so 0 is an empty wait.
    hand = ready_hand("0 + 1 1 0 x 5 0 2 x 3 6 0")

    is_ready, ready_info = checker.is_ready(hand)

    assert is_ready
    assert "算术麻将" in ready_info
    assert "0（空听）" in ready_info["算术麻将"]


def test_ready_tile_17_can_be_empty_listening():
    checker = make_checker()
    hand = ready_hand("10 + 7 17 10 + 7 17 5 + 12 7 7")

    is_ready, ready_info = checker.is_ready(hand)

    assert is_ready
    assert "算术麻将" in ready_info
    assert "17（空听）" in ready_info["算术麻将"]


def test_ready_for_qing_long_special_shape():
    checker = make_checker()
    hand = ready_hand("1 2 3 4 5 6 7 8 9 10 11 12 16")

    is_ready, ready_info = checker.is_ready(hand)

    assert is_ready
    assert "清龙" in ready_info
    assert ready_info["清龙"] == ["16"]


def test_return_details_only_checks_ready_not_fan_requirement():
    checker = make_checker()
    hand = ready_hand("1 + 9 10 2 x 3 6 4 4 4 4 5")

    is_ready, ready_info = checker.is_ready(hand, return_details=True)

    assert is_ready
    assert "算术麻将" in ready_info
    assert set(ready_info["算术麻将"]["tiles"]) == {1, 5, "×"}
    for detail in ready_info["算术麻将"]["details"].values():
        assert detail["groups"]


def test_san_men_qi_ready_with_kezi_plus_formula_and_multiply_formula():
    checker = ArithmeticMahjong(min_fan=1)
    hand = ready_hand_with_meld("(1 + 9 10) (2 3 6 x) 4 4 4 4 +")

    is_ready, ready_info = checker.is_ready(hand, return_details=True)

    assert is_ready
    assert "算术麻将" in ready_info
    assert "+" in ready_info["算术麻将"]["tiles"]

    fan_info = ready_info["算术麻将"]["details"]["+"]["fan_info"]
    fan_types = {fan.fan_type for fan in fan_info["fan_result"].results}
    assert FanType.SAN_MEN_QI in fan_types
    assert fan_info["can_start"]
