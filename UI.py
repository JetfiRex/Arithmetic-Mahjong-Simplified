"""
Command-line UI for the simplified arithmetic mahjong calculator.
"""

from calculator_base.mahjong_checker import ArithmeticMahjong
from calculator_base.parser import (
    parse_mode1_already_won,
    parse_mode2_check_win,
    parse_mode3_ready_with_meld,
    parse_mode4_ready_no_meld,
)
from fan_calculator import calculate_fan


LINE_WIDTH = 70
ALLOWED_WINNING_METHODS = {None, "自摸", "天胡"}


def print_welcome():
    print("=" * LINE_WIDTH)
    print("算术麻将简单版胡牌/听牌/番数计算器".center(LINE_WIDTH))
    print("=" * LINE_WIDTH)
    print()


def print_help():
    print("输入模式")
    print("-" * LINE_WIDTH)
    print("1. 已胡番数模式：已分组，计算番种和筹码")
    print("2. 胡牌判定模式：未分组，自动尝试算术麻将/传统麻将/特殊胡法")
    print("3. 有鸣牌听牌模式：输入鸣牌和剩余手牌，只判断听什么")
    print("4. 无鸣牌听牌模式：输入未鸣牌手牌，只判断听什么")
    print()
    print("牌张")
    print("  数字: 0-20, 24")
    print("  符号: +, x, X, *, × 都可输入；内部统一为 ×")
    print("  简单版没有宝牌、万用牌、替换牌、次方牌")
    print()
    print("分组/标记")
    print("  (牌)       鸣牌，例如 (1 + 9 10), (4 4 4 4), (4 4 4 4 4 暗)")
    print("  / 或 |     已分组手牌的分组分隔符")
    print("  [牌]       胡牌标记，可选")
    print("  {方式}     胡牌方式，只支持 {自摸} 和 {天胡}")
    print("             短别名: {z}/{zm}/{zimo}=自摸, {t}/{th}=天胡")
    print()
    print("起胡")
    print("  默认 1 番起胡。形状能胡但 0 番时，UI 会保留结果并给出警告。")
    print("-" * LINE_WIDTH)
    print()


def choose_mode():
    print("选择输入模式")
    print("1. 已胡番数模式")
    print("2. 胡牌判定模式")
    print("3. 有鸣牌听牌模式")
    print("4. 无鸣牌听牌模式")
    print("q. 退出")

    while True:
        choice = input("请选择模式 (1-4/q): ").strip().lower()
        if choice in {"1", "2", "3", "4", "q", "quit", "exit"}:
            return "q" if choice in {"q", "quit", "exit"} else choice
        print("无效选择，请输入 1-4 或 q")


def ensure_supported_winning_method(hand):
    if hand.winning_method not in ALLOWED_WINNING_METHODS:
        raise ValueError(
            f"简单版 UI 只支持 {{自摸}} 和 {{天胡}}，当前为 {{{hand.winning_method}}}"
        )


def print_melded_groups(hand):
    if not hand.melded_groups:
        return

    print("鸣牌:")
    for idx, group in enumerate(hand.melded_groups, 1):
        tiles = " ".join(str(tile.value) for tile in group.tiles)
        print(f"  {idx}. {group.group_type}: {tiles}")


def print_hand_groups(groups, checker=None):
    for idx, group in enumerate(groups, 1):
        group_text = " ".join(str(tile) for tile in group)
        if checker is None or not isinstance(group, list):
            print(f"  第{idx}组: {group_text}")
        elif checker.is_pair(group):
            print(f"  第{idx}组（对子）: {group_text}")
        elif checker.is_kezi(group):
            print(f"  第{idx}组（刻子）: {group_text}")
        elif checker.is_valid_formula(group):
            print(f"  第{idx}组（算式）: {group_text}")
        else:
            print(f"  第{idx}组: {group_text}")


def print_fan_result(result, min_fan=1):
    total = result.get_total_fan()
    print(f"总番: {total}番")
    print(f"封顶后: {result.get_capped_fan()}番")
    print(f"应赔付筹码: {result.get_payment()}")

    if total >= min_fan:
        print(f"满足起胡条件（{min_fan}番起胡）")
    else:
        print(f"警告: 不满足起胡条件（需要{min_fan}番，当前{total}番）")

    if result.results:
        print("番种明细:")
        for fan in result.results:
            print(f"  {fan}")
    else:
        print("没有满足的番种")

    if result.excluded:
        print("被排除的番种:")
        for fan_type, reason in result.excluded:
            print(f"  {fan_type.fan_name}: {reason}")


def print_fan_info(fan_info, min_fan=1):
    if not fan_info:
        print("番数计算不可用")
        return

    print(f"总番: {fan_info.get('total_fan', 0)}番")
    print(f"封顶后: {fan_info.get('capped_fan', 0)}番")
    print(f"应赔付筹码: {fan_info.get('payment', 0)}")

    if fan_info.get("can_start", False):
        print(f"满足起胡条件（{min_fan}番起胡）")
    else:
        print(
            f"警告: 不满足起胡条件（需要{min_fan}番，当前{fan_info.get('total_fan', 0)}番）"
        )

    fan_result = fan_info.get("fan_result")
    if fan_result and fan_result.results:
        print("番种明细:")
        for fan in fan_result.results:
            print(f"  {fan}")
    else:
        print("没有满足的番种")

    if fan_result and fan_result.excluded:
        print("被排除的番种:")
        for fan_type, reason in fan_result.excluded:
            print(f"  {fan_type.fan_name}: {reason}")


def read_hand(prompt):
    text = input(prompt).strip()
    if text.lower() in {"q", "quit", "exit"}:
        return None
    return text


def mode1_already_won(checker):
    print()
    print("=" * LINE_WIDTH)
    print("模式1: 已胡番数模式")
    print("=" * LINE_WIDTH)
    print("格式: (鸣牌) 手牌组 / 手牌组 / 对子 [胡牌] {方式}")
    print("示例: 1 + 9 10 / 2 x 3 6 / 4 4 4 4 / 5 [5] {自摸}")
    print("返回: 直接回车；退出: q")
    print()

    while True:
        hand_str = read_hand("请输入已分组手牌: ")
        if hand_str is None:
            return False
        if not hand_str:
            return True

        try:
            hand = parse_mode1_already_won(hand_str)
            ensure_supported_winning_method(hand)

            print()
            print("-" * LINE_WIDTH)
            print_melded_groups(hand)
            if hand.hand_groups:
                print("手牌分组:")
                print_hand_groups(hand.hand_groups, checker)
            if hand.winning_tile:
                print(f"胡牌: {hand.winning_tile.value}")
            if hand.winning_method:
                print(f"胡牌方式: {hand.winning_method}")
            print("-" * LINE_WIDTH)

            result = calculate_fan(hand, min_fan=checker.min_fan)
            print_fan_result(result, min_fan=checker.min_fan)
            print("=" * LINE_WIDTH)
            return True
        except ValueError as exc:
            print(f"解析错误: {exc}")
        except Exception as exc:
            print(f"发生错误: {exc}")


def mode2_win_check(checker):
    print()
    print("=" * LINE_WIDTH)
    print("模式2: 胡牌判定模式")
    print("=" * LINE_WIDTH)
    print("格式: 14张牌，允许鸣牌括号；未分组会自动尝试组牌")
    print("示例: 1 + 9 10 2 x 3 6 4 4 4 4 5 5")
    print("返回: 直接回车；退出: q")
    print()

    while True:
        hand_str = read_hand("请输入手牌: ")
        if hand_str is None:
            return False
        if not hand_str:
            return True

        try:
            hand = parse_mode2_check_win(hand_str)
            ensure_supported_winning_method(hand)

            can_win, groups, win_type, fan_info = checker.can_win(hand)

            print()
            print("-" * LINE_WIDTH)
            if not can_win:
                print("无法胡牌")
                print("=" * LINE_WIDTH)
                return True

            print(f"可以胡牌: {win_type}")
            if groups:
                print("胡牌分组:")
                print_hand_groups(groups, checker)
            print("-" * LINE_WIDTH)
            print_fan_info(fan_info, min_fan=checker.min_fan)
            print("=" * LINE_WIDTH)
            return True
        except ValueError as exc:
            print(f"解析错误: {exc}")
        except Exception as exc:
            print(f"发生错误: {exc}")


def mode3_ready_with_melded(checker):
    print()
    print("=" * LINE_WIDTH)
    print("模式3: 有鸣牌听牌模式")
    print("=" * LINE_WIDTH)
    print("格式: (鸣牌) 剩余手牌")
    print("示例: (1 + 9 10) (2 x 3 6) 4 4 4 4 5")
    print("返回: 直接回车；退出: q")
    print()

    while True:
        hand_str = read_hand("请输入听牌手牌: ")
        if hand_str is None:
            return False
        if not hand_str:
            return True

        try:
            hand = parse_mode3_ready_with_meld(hand_str)
            print_ready_result(checker, hand)
            return True
        except ValueError as exc:
            print(f"解析错误: {exc}")
        except Exception as exc:
            print(f"发生错误: {exc}")


def mode4_ready_no_melded(checker):
    print()
    print("=" * LINE_WIDTH)
    print("模式4: 无鸣牌听牌模式")
    print("=" * LINE_WIDTH)
    print("格式: 13张牌，无括号")
    print("示例: 1 + 9 10 2 x 3 6 4 4 4 4 5")
    print("返回: 直接回车；退出: q")
    print()

    while True:
        hand_str = read_hand("请输入听牌手牌: ")
        if hand_str is None:
            return False
        if not hand_str:
            return True

        try:
            hand = parse_mode4_ready_no_meld(hand_str)
            print_ready_result(checker, hand)
            return True
        except ValueError as exc:
            print(f"解析错误: {exc}")
        except Exception as exc:
            print(f"发生错误: {exc}")


def print_ready_result(checker, hand):
    is_ready, ready_info = checker.is_ready(hand, return_details=True)

    all_tiles = []
    for group in hand.melded_groups:
        all_tiles.extend(tile.value for tile in group.tiles)
    all_tiles.extend(tile.value for tile in hand.hand_tiles)

    print()
    print("-" * LINE_WIDTH)
    print(f"当前牌: {' '.join(str(tile) for tile in all_tiles)}")
    print("-" * LINE_WIDTH)

    if not is_ready:
        print("未听牌")
        print("=" * LINE_WIDTH)
        return

    print("听牌:")
    for win_type, info in ready_info.items():
        print(f"【{win_type}】")
        for tile in info["tiles"]:
            detail = info["details"][tile]
            fan_info = detail.get("fan_info") or {}
            label = str(tile)
            if not fan_info.get("can_start", False):
                label += "（不满足1番起胡）"
            print(f"  {label}")
    print("=" * LINE_WIDTH)


def main():
    checker = ArithmeticMahjong(min_fan=1)

    print_welcome()
    print_help()

    while True:
        mode = choose_mode()
        if mode == "q":
            break

        if mode == "1":
            should_continue = mode1_already_won(checker)
        elif mode == "2":
            should_continue = mode2_win_check(checker)
        elif mode == "3":
            should_continue = mode3_ready_with_melded(checker)
        else:
            should_continue = mode4_ready_no_melded(checker)

        if not should_continue:
            break

        print()
        again = input("是否继续？(y/n) [默认 y]: ").strip().lower()
        if again in {"n", "no", "q", "quit", "exit"}:
            break
        print()

    print()
    print("=" * LINE_WIDTH)
    print("已退出".center(LINE_WIDTH))
    print("=" * LINE_WIDTH)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已中断")
