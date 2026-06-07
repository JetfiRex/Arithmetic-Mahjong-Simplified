"""
Kivy mobile app for the simplified arithmetic mahjong calculator.

This file is intentionally separate from the Tkinter desktop GUI. It reuses
the existing calculator modules and provides a touch-oriented interface that
can be packaged for Android with Buildozer.
"""

from pathlib import Path

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from calculator_base.constants import ALL_TILES, SYMBOLS, TILE_COUNTS
from calculator_base.empty_listening_checker import analyze_ready_tiles
from calculator_base.hand_structure import Hand, MeldedGroup, create_tile_from_value
from calculator_base.mahjong_checker import ArithmeticMahjong
from calculator_base.parser import tile_sort_key


MIN_FAN = 1


def register_cjk_font():
    """Use a CJK-capable system font when available."""
    candidates = [
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("/system/fonts/NotoSansCJK-Regular.ttc"),
        Path("/system/fonts/NotoSansCJK-Regular.otf"),
        Path("/system/fonts/DroidSansFallback.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    ]
    for font_path in candidates:
        if font_path.exists():
            LabelBase.register(name="Roboto", fn_regular=str(font_path))
            return


def sorted_tiles():
    return sorted(ALL_TILES, key=lambda value: (value in SYMBOLS, tile_sort_key(value)))


def tile_text(value):
    return str(value)


class MahjongMobileRoot(BoxLayout):
    status_text = StringProperty("请选择模式和目标，然后点牌。")

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(8), **kwargs)
        self.checker = ArithmeticMahjong(min_fan=MIN_FAN)
        self.mode = "2"
        self.target = "hand"
        self.meld_type = "吃"
        self.winning_method = ""

        self.hand_tiles = []
        self.current_group = []
        self.hand_groups = []
        self.current_meld = []
        self.melded_groups = []

        self._build_layout()
        self._refresh_state()

    def _build_layout(self):
        self.add_widget(self._build_mode_row())
        self.add_widget(self._build_target_row())
        self.add_widget(self._build_tile_palette())
        self.add_widget(self._build_state_panel())
        self.add_widget(self._build_action_panel())
        self.add_widget(self._build_output())

    def _build_mode_row(self):
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.mode_spinner = Spinner(
            text="2 胡牌判定",
            values=("1 已胡番数", "2 胡牌判定", "3 有鸣牌听牌", "4 无鸣牌听牌"),
        )
        self.mode_spinner.bind(text=self._on_mode_changed)

        self.winning_spinner = Spinner(
            text="胡牌方式: 无",
            values=("胡牌方式: 无", "胡牌方式: 点胡", "胡牌方式: 自摸", "胡牌方式: 天胡"),
        )
        self.winning_spinner.bind(text=self._on_winning_method_changed)

        row.add_widget(self.mode_spinner)
        row.add_widget(self.winning_spinner)
        return row

    def _build_target_row(self):
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.target_spinner = Spinner(
            text="目标: 手牌区",
            values=("目标: 手牌区", "目标: 当前分组", "目标: 当前鸣牌"),
        )
        self.target_spinner.bind(text=self._on_target_changed)

        self.meld_spinner = Spinner(text="鸣牌: 吃", values=("鸣牌: 吃", "鸣牌: 碰", "鸣牌: 明杠", "鸣牌: 暗杠"))
        self.meld_spinner.bind(text=self._on_meld_type_changed)

        row.add_widget(self.target_spinner)
        row.add_widget(self.meld_spinner)
        return row

    def _build_tile_palette(self):
        scroll = ScrollView(size_hint_y=None, height=dp(190))
        grid = GridLayout(cols=6, spacing=dp(6), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        for value in sorted_tiles():
            button = Button(text=tile_text(value), size_hint_y=None, height=dp(44), font_size=dp(17))
            button.bind(on_release=lambda _button, tile=value: self._add_tile(tile))
            grid.add_widget(button)

        scroll.add_widget(grid)
        return scroll

    def _build_state_panel(self):
        self.state_label = Label(
            text="",
            size_hint_y=None,
            height=dp(132),
            halign="left",
            valign="top",
            font_size=dp(14),
        )
        self.state_label.bind(size=lambda label, _size: setattr(label, "text_size", label.size))
        return self.state_label

    def _build_action_panel(self):
        grid = GridLayout(cols=3, size_hint_y=None, height=dp(92), spacing=dp(6))
        actions = [
            ("确认分组", self._commit_group),
            ("确认鸣牌", self._commit_meld),
            ("撤销一张", self._undo_active),
            ("清空目标", self._clear_active),
            ("全部清空", self._clear_all),
            ("计算", self._calculate),
        ]
        for text, callback in actions:
            button = Button(text=text, font_size=dp(14))
            button.bind(on_release=lambda _button, fn=callback: fn())
            grid.add_widget(button)
        return grid

    def _build_output(self):
        self.output = TextInput(
            text="",
            readonly=True,
            size_hint_y=1,
            font_size=dp(14),
            background_color=(0.96, 0.93, 0.86, 1),
            foreground_color=(0.08, 0.07, 0.05, 1),
        )
        return self.output

    def _on_mode_changed(self, _spinner, text):
        self.mode = text.split(" ", 1)[0]
        if self.mode == "1":
            self.target = "group"
            self.target_spinner.text = "目标: 当前分组"
        else:
            self.target = "hand"
            self.target_spinner.text = "目标: 手牌区"
        self._refresh_state()

    def _on_target_changed(self, _spinner, text):
        if "手牌区" in text:
            self.target = "hand"
        elif "当前分组" in text:
            self.target = "group"
        else:
            self.target = "meld"
        self._refresh_state()

    def _on_meld_type_changed(self, _spinner, text):
        self.meld_type = text.replace("鸣牌: ", "")
        self._refresh_state()

    def _on_winning_method_changed(self, _spinner, text):
        self.winning_method = "" if text.endswith("无") else text.replace("胡牌方式: ", "")
        self._refresh_state()

    def _add_tile(self, value):
        if self._used_count(value) >= TILE_COUNTS[value]:
            self._show_message("牌数不足", f"{value} 已达到牌堆上限 {TILE_COUNTS[value]} 张")
            return

        if self.target == "hand":
            self.hand_tiles.append(value)
        elif self.target == "group":
            self.current_group.append(value)
        else:
            self.current_meld.append(value)
        self._refresh_state()

    def _commit_group(self, *_args):
        if not self.current_group:
            self._show_message("没有分组", "当前分组为空")
            return
        self.hand_groups.append(list(self.current_group))
        self.current_group.clear()
        self._refresh_state()

    def _commit_meld(self, *_args):
        if not self.current_meld:
            self._show_message("没有鸣牌", "当前鸣牌为空")
            return

        expected_len = 5 if self.meld_type in {"明杠", "暗杠"} else 4
        if len(self.current_meld) != expected_len:
            self._show_message("鸣牌张数错误", f"{self.meld_type} 需要 {expected_len} 张，当前 {len(self.current_meld)} 张")
            return

        try:
            tiles = [create_tile_from_value(value) for value in self.current_meld]
            self.melded_groups.append(MeldedGroup(tiles, self.meld_type))
        except ValueError as exc:
            self._show_message("鸣牌错误", str(exc))
            return

        self.current_meld.clear()
        self._refresh_state()

    def _undo_active(self, *_args):
        target = self._active_list()
        if target:
            target.pop()
        self._refresh_state()

    def _clear_active(self, *_args):
        self._active_list().clear()
        self._refresh_state()

    def _clear_all(self, *_args):
        self.hand_tiles.clear()
        self.current_group.clear()
        self.hand_groups.clear()
        self.current_meld.clear()
        self.melded_groups.clear()
        self.output.text = ""
        self._refresh_state()

    def _calculate(self, *_args):
        try:
            if self.mode == "1":
                self._calculate_grouped_win()
            elif self.mode == "2":
                self._calculate_win_check()
            elif self.mode == "3":
                self._calculate_ready(with_melds=True)
            else:
                self._calculate_ready(with_melds=False)
        except ValueError as exc:
            self._show_message("输入错误", str(exc))
        except Exception as exc:
            self._show_message("计算错误", str(exc))

    def _calculate_grouped_win(self):
        self._ensure_no_uncommitted()
        hand = self._make_hand(hand_groups=self.hand_groups)
        success, groups, win_type, fan_info = self.checker.can_win(hand)

        lines = ["模式1：已胡番数", ""]
        if not success:
            lines.append("无法胡牌：分组或牌型不符合简单版规则")
            self.output.text = "\n".join(lines)
            return

        lines.append(f"可以胡牌：{win_type}")
        lines.append("")
        lines.extend(self._format_groups(groups))
        lines.append("")
        lines.extend(self._format_fan_info(fan_info))
        self.output.text = "\n".join(lines)

    def _calculate_win_check(self):
        self._ensure_no_uncommitted()
        if self.hand_groups:
            raise ValueError("模式2使用未分组手牌；如需使用分组，请切换到模式1")

        hand = self._make_hand(hand_tiles=self.hand_tiles)
        success, groups, win_type, fan_info = self.checker.can_win(hand)

        lines = ["模式2：胡牌判定", ""]
        if not success:
            lines.append("无法胡牌")
            self.output.text = "\n".join(lines)
            return

        lines.append(f"可以胡牌：{win_type}")
        lines.append("")
        lines.extend(self._format_groups(groups))
        lines.append("")
        lines.extend(self._format_fan_info(fan_info))
        self.output.text = "\n".join(lines)

    def _calculate_ready(self, with_melds):
        self._ensure_no_uncommitted()
        if self.hand_groups:
            raise ValueError("听牌模式不使用已分组手牌，请清空分组")
        if not with_melds and self.melded_groups:
            raise ValueError("模式4是无鸣牌听牌，请清空鸣牌或切换到模式3")

        hand = self._make_hand(hand_tiles=self.hand_tiles, include_melds=with_melds)
        is_ready, ready_info = self.checker.is_ready(hand, return_details=True)

        lines = [f"模式{'3' if with_melds else '4'}：听牌判定", ""]
        if not is_ready:
            lines.append("未听牌")
            self.output.text = "\n".join(lines)
            return

        visible_tiles = self._visible_tile_values(hand)
        lines.append("听牌：")
        for win_type, info in ready_info.items():
            availability = analyze_ready_tiles(info["tiles"], visible_tiles)
            lines.append(f"【{win_type}】")
            for tile_value in info["tiles"]:
                detail = info["details"][tile_value]
                fan_text = self._short_fan_text(detail.get("fan_info"))
                display_tile = availability[tile_value]["display"]
                lines.append(f"  {display_tile}: {fan_text}")
            lines.append("")

        self.output.text = "\n".join(lines).rstrip()

    def _make_hand(self, hand_tiles=None, hand_groups=None, include_melds=True):
        return Hand(
            melded_groups=list(self.melded_groups) if include_melds else [],
            hand_tiles=[create_tile_from_value(value) for value in (hand_tiles or [])],
            hand_groups=[
                [create_tile_from_value(value) for value in group]
                for group in (hand_groups or [])
            ],
            winning_method=self.winning_method or None,
            should_win_in_mode=self.mode in {"1", "2"},
        )

    def _ensure_no_uncommitted(self):
        if self.current_group:
            raise ValueError("当前分组尚未确认")
        if self.current_meld:
            raise ValueError("当前鸣牌尚未确认")

    def _format_groups(self, groups):
        if not groups:
            return ["无分组信息"]

        lines = ["胡牌分组:"]
        for idx, group in enumerate(groups, 1):
            if isinstance(group, MeldedGroup):
                values = " ".join(str(tile.value) for tile in group.tiles)
                lines.append(f"  {idx}. {group.group_type}: {values}")
                continue

            values = " ".join(str(tile) for tile in group)
            if self.checker.is_pair(group):
                group_type = "对子"
            elif self.checker.is_kezi(group):
                group_type = "刻子"
            elif self.checker.is_valid_formula(group):
                group_type = "算式"
            else:
                group_type = "组合"
            lines.append(f"  {idx}. {group_type}: {values}")
        return lines

    def _format_fan_info(self, fan_info):
        if not fan_info:
            return ["番数计算不可用"]

        lines = [
            f"总番: {fan_info.get('total_fan', 0)}番",
            f"封顶后: {fan_info.get('capped_fan', 0)}番",
            f"应赔付筹码: {fan_info.get('payment', 0)}",
        ]
        if fan_info.get("can_start", False):
            lines.append(f"满足起胡条件（{MIN_FAN}番起胡）")
        else:
            lines.append(f"警告: 不满足起胡条件（需要{MIN_FAN}番）")

        fan_result = fan_info.get("fan_result")
        if fan_result and fan_result.results:
            lines.append("番种明细:")
            lines.extend(f"  {fan}" for fan in fan_result.results)
        else:
            lines.append("没有满足的番种")

        if fan_result and fan_result.excluded:
            lines.append("被排除的番种:")
            lines.extend(f"  {fan_type.fan_name}: {reason}" for fan_type, reason in fan_result.excluded)

        return lines

    @staticmethod
    def _short_fan_text(fan_info):
        if not fan_info:
            return "番数不可用"
        total = fan_info.get("total_fan", 0)
        payment = fan_info.get("payment", 0)
        status = "可起胡" if fan_info.get("can_start", False) else "未起胡"
        return f"{total}番，{payment}筹码，{status}"

    @staticmethod
    def _visible_tile_values(hand):
        values = []
        for group in hand.melded_groups:
            values.extend(tile.value for tile in group.tiles)
        values.extend(tile.value for tile in hand.hand_tiles)
        return values

    def _refresh_state(self):
        self.state_label.text = "\n".join(
            [
                f"手牌区: {self._format_values(self.hand_tiles)}",
                f"当前分组: {self._format_values(self.current_group)}",
                f"已确认分组: {self._format_groups_summary()}",
                f"当前鸣牌: {self._format_values(self.current_meld)}",
                f"已确认鸣牌: {self._format_melds_summary()}",
                f"当前目标: {self._target_display()}",
            ]
        )

    def _format_values(self, values):
        return " ".join(str(value) for value in values) if values else "空"

    def _format_groups_summary(self):
        if not self.hand_groups:
            return "空"
        return " | ".join(self._format_values(group) for group in self.hand_groups)

    def _format_melds_summary(self):
        if not self.melded_groups:
            return "空"
        return " | ".join(f"{group.group_type}: {' '.join(str(tile.value) for tile in group.tiles)}" for group in self.melded_groups)

    def _target_display(self):
        return {"hand": "手牌区", "group": "当前分组", "meld": "当前鸣牌"}[self.target]

    def _active_list(self):
        if self.target == "hand":
            return self.hand_tiles
        if self.target == "group":
            return self.current_group
        return self.current_meld

    def _used_count(self, value):
        count = self.hand_tiles.count(value)
        count += self.current_group.count(value)
        count += sum(group.count(value) for group in self.hand_groups)
        count += self.current_meld.count(value)
        count += sum(1 for group in self.melded_groups for tile in group.tiles if tile.value == value)
        return count

    def _show_message(self, title, message):
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        label = Label(text=message, halign="center", valign="middle")
        label.bind(size=lambda widget, _size: setattr(widget, "text_size", widget.size))
        close_button = Button(text="关闭", size_hint_y=None, height=dp(42))
        content.add_widget(label)
        content.add_widget(close_button)
        popup = Popup(title=title, content=content, size_hint=(0.86, None), height=dp(210))
        close_button.bind(on_release=popup.dismiss)
        popup.open()


class SuanshuMahjongMobileApp(App):
    def build(self):
        self.title = "算术麻将简单版"
        return MahjongMobileRoot()


if __name__ == "__main__":
    register_cjk_font()
    SuanshuMahjongMobileApp().run()
