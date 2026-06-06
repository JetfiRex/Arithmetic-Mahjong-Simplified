"""
Tkinter GUI for the simplified arithmetic mahjong calculator.

The command-line UI remains in UI.py as a backup. This file is intentionally
standalone and uses only the standard library plus the existing calculator
modules.
"""

import tkinter as tk
import sys
from pathlib import Path
from tkinter import messagebox, ttk

from calculator_base.constants import ALL_TILES, SYMBOLS, TILE_COUNTS
from calculator_base.empty_listening_checker import analyze_ready_tiles
from calculator_base.hand_structure import Hand, MeldedGroup, create_tile_from_value
from calculator_base.mahjong_checker import ArithmeticMahjong
from calculator_base.parser import tile_sort_key


MIN_FAN = 1
TILE_W = 50
TILE_H = 72
TILE_GAP = 6
BUTTON_IMAGE_SUBSAMPLE = 14
TABLE_IMAGE_SUBSAMPLE = 10
BUTTON_W = 78
BUTTON_H = 112


def app_base_dir():
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


PICTURES_DIR = app_base_dir() / "pictures"
APP_ICON_PNG = PICTURES_DIR / "app_icon.png"
APP_ICON_ICO = PICTURES_DIR / "app_icon.ico"


def sorted_tiles():
    return sorted(ALL_TILES, key=lambda value: (value in SYMBOLS, tile_sort_key(value)))


class MahjongGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("算术麻将简单版 GUI")
        self._set_app_icon()
        self.geometry("1180x780")
        self.minsize(980, 680)

        self.checker = ArithmeticMahjong(min_fan=MIN_FAN)
        self.mode = tk.StringVar(value="2")
        self.target = tk.StringVar(value="hand")
        self.meld_type = tk.StringVar(value="吃")
        self.winning_method = tk.StringVar(value="")

        self.hand_tiles = []
        self.current_group = []
        self.hand_groups = []
        self.current_meld = []
        self.melded_groups = []
        self.tile_buttons = {}
        self.button_images = {}
        self.table_images = {}
        self.rotated_table_images = {}

        self._build_layout()
        self._load_tile_images()
        self._populate_tile_palette()
        self._refresh_all()

    def _set_app_icon(self):
        self.app_icon_image = None
        if APP_ICON_PNG.exists():
            try:
                self.app_icon_image = tk.PhotoImage(file=str(APP_ICON_PNG))
                self.iconphoto(True, self.app_icon_image)
            except tk.TclError:
                self.app_icon_image = None

        if APP_ICON_ICO.exists():
            try:
                self.iconbitmap(str(APP_ICON_ICO))
            except tk.TclError:
                pass

    def _build_layout(self):
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        left = self._build_scrollable_left()

        right = ttk.Frame(self, padding=(0, 10, 10, 10))
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=3)
        right.rowconfigure(1, weight=2)
        right.columnconfigure(0, weight=1)

        self._build_mode_panel(left)
        self._build_target_panel(left)
        self._build_tile_palette(left)
        self._build_action_panel(left)

        canvas_frame = ttk.Frame(right)
        canvas_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#f7f1e4",
            highlightthickness=1,
            highlightbackground="#b9ad9a",
            height=360,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        canvas_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        canvas_scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=canvas_scrollbar.set)

        self.output = tk.Text(right, wrap="word", height=16, font=("Microsoft YaHei UI", 10))
        self.output.grid(row=1, column=0, sticky="nsew")

    def _build_scrollable_left(self):
        outer = ttk.Frame(self)
        outer.grid(row=0, column=0, sticky="ns")
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)

        left_canvas = tk.Canvas(outer, width=620, highlightthickness=0)
        left_canvas.grid(row=0, column=0, sticky="ns")

        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=left_canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        left_canvas.configure(yscrollcommand=scrollbar.set)

        left = ttk.Frame(left_canvas, padding=10)
        window_id = left_canvas.create_window((0, 0), window=left, anchor="nw")

        def update_scroll_region(event=None):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))
            left_canvas.itemconfigure(window_id, width=left_canvas.winfo_width())

        left.bind("<Configure>", update_scroll_region)
        left_canvas.bind("<Configure>", update_scroll_region)
        left_canvas.bind_all("<MouseWheel>", lambda event: left_canvas.yview_scroll(int(-event.delta / 120), "units"))

        return left

    def _build_mode_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="模式", padding=8)
        frame.pack(fill="x", pady=(0, 8))

        modes = [
            ("1 已胡番数", "1"),
            ("2 胡牌判定", "2"),
            ("3 有鸣牌听牌", "3"),
            ("4 无鸣牌听牌", "4"),
        ]
        for text, value in modes:
            ttk.Radiobutton(
                frame,
                text=text,
                value=value,
                variable=self.mode,
                command=self._on_mode_changed,
            ).pack(anchor="w")

    def _build_target_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="点牌目标", padding=8)
        frame.pack(fill="x", pady=(0, 8))

        ttk.Radiobutton(frame, text="手牌区", value="hand", variable=self.target).pack(anchor="w")
        ttk.Radiobutton(frame, text="当前分组（模式1）", value="group", variable=self.target).pack(anchor="w")
        ttk.Radiobutton(frame, text="当前鸣牌", value="meld", variable=self.target).pack(anchor="w")

        ttk.Label(frame, text="鸣牌类型").pack(anchor="w", pady=(8, 2))
        ttk.Combobox(
            frame,
            textvariable=self.meld_type,
            values=("吃", "碰", "明杠", "暗杠"),
            state="readonly",
            width=8,
        ).pack(anchor="w")

        ttk.Label(frame, text="胡牌方式").pack(anchor="w", pady=(8, 2))
        ttk.Combobox(
            frame,
            textvariable=self.winning_method,
            values=("", "点胡", "自摸", "天胡"),
            state="readonly",
            width=8,
        ).pack(anchor="w")

    def _build_tile_palette(self, parent):
        self.tile_palette_frame = ttk.LabelFrame(parent, text="牌面", padding=8)
        self.tile_palette_frame.pack(fill="x", pady=(0, 8))

    def _populate_tile_palette(self):
        for idx, tile in enumerate(sorted_tiles()):
            button = tk.Button(
                self.tile_palette_frame,
                width=4,
                relief="raised",
                command=lambda value=tile: self._add_tile(value),
            )
            button.grid(row=idx // 6, column=idx % 6, padx=2, pady=2)
            self.tile_buttons[tile] = button

    def _load_tile_images(self):
        for tile_value in sorted_tiles():
            image_path = self._tile_image_path(tile_value)
            if not image_path.exists():
                continue

            try:
                raw = tk.PhotoImage(file=str(image_path))
                self.button_images[tile_value] = raw.subsample(
                    BUTTON_IMAGE_SUBSAMPLE,
                    BUTTON_IMAGE_SUBSAMPLE,
                )
                self.table_images[tile_value] = raw.subsample(
                    TABLE_IMAGE_SUBSAMPLE,
                    TABLE_IMAGE_SUBSAMPLE,
                )
            except tk.TclError:
                continue

    @staticmethod
    def _tile_image_path(tile_value):
        if tile_value == "+":
            filename = "plus.png"
        elif tile_value == "×":
            filename = "mult.png"
        else:
            filename = f"{tile_value}.png"
        return PICTURES_DIR / filename

    def _build_action_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="操作", padding=8)
        frame.pack(fill="x")

        ttk.Button(frame, text="确认分组", command=self._commit_group).pack(fill="x", pady=2)
        ttk.Button(frame, text="确认鸣牌", command=self._commit_meld).pack(fill="x", pady=2)
        ttk.Button(frame, text="撤销当前目标一张", command=self._undo_active).pack(fill="x", pady=2)
        ttk.Button(frame, text="清空当前目标", command=self._clear_active).pack(fill="x", pady=2)
        ttk.Separator(frame).pack(fill="x", pady=6)
        ttk.Button(frame, text="计算", command=self._calculate).pack(fill="x", pady=2)
        ttk.Button(frame, text="全部清空", command=self._clear_all).pack(fill="x", pady=2)

        self.status_label = ttk.Label(frame, text="", justify="left")
        self.status_label.pack(fill="x", pady=(8, 0))

    def _on_mode_changed(self):
        if self.mode.get() == "1":
            self.target.set("group")
        else:
            self.target.set("hand")
        self._refresh_all()

    def _add_tile(self, value):
        if self._used_count(value) >= TILE_COUNTS[value]:
            messagebox.showwarning("牌数不足", f"{value} 已达到牌堆上限 {TILE_COUNTS[value]} 张")
            return

        target = self.target.get()
        if target == "hand":
            self.hand_tiles.append(value)
        elif target == "group":
            self.current_group.append(value)
        else:
            self.current_meld.append(value)

        self._refresh_all()

    def _commit_group(self):
        if not self.current_group:
            messagebox.showinfo("没有分组", "当前分组为空")
            return
        self.hand_groups.append(list(self.current_group))
        self.current_group.clear()
        self._refresh_all()

    def _commit_meld(self):
        if not self.current_meld:
            messagebox.showinfo("没有鸣牌", "当前鸣牌为空")
            return

        group_type = self.meld_type.get()
        expected_len = 5 if group_type in {"明杠", "暗杠"} else 4
        if len(self.current_meld) != expected_len:
            messagebox.showerror(
                "鸣牌张数错误",
                f"{group_type} 需要 {expected_len} 张，当前 {len(self.current_meld)} 张",
            )
            return

        try:
            tiles = [create_tile_from_value(value) for value in self.current_meld]
            self.melded_groups.append(MeldedGroup(tiles, group_type))
        except ValueError as exc:
            messagebox.showerror("鸣牌错误", str(exc))
            return

        self.current_meld.clear()
        self._refresh_all()

    def _undo_active(self):
        target_list = self._active_list()
        if target_list:
            target_list.pop()
        self._refresh_all()

    def _clear_active(self):
        self._active_list().clear()
        self._refresh_all()

    def _clear_all(self):
        self.hand_tiles.clear()
        self.current_group.clear()
        self.hand_groups.clear()
        self.current_meld.clear()
        self.melded_groups.clear()
        self._write_output("")
        self._refresh_all()

    def _active_list(self):
        target = self.target.get()
        if target == "hand":
            return self.hand_tiles
        if target == "group":
            return self.current_group
        return self.current_meld

    def _calculate(self):
        try:
            mode = self.mode.get()
            if mode == "1":
                self._calculate_grouped_win()
            elif mode == "2":
                self._calculate_win_check()
            elif mode == "3":
                self._calculate_ready(with_melds=True)
            else:
                self._calculate_ready(with_melds=False)
        except ValueError as exc:
            messagebox.showerror("输入错误", str(exc))
        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))

    def _calculate_grouped_win(self):
        self._ensure_no_uncommitted()
        hand = self._make_hand(hand_groups=self.hand_groups)
        success, groups, win_type, fan_info = self.checker.can_win(hand)

        lines = ["模式1：已胡番数", ""]
        if not success:
            lines.append("无法胡牌：分组或牌型不符合简单版规则")
            self._write_output("\n".join(lines))
            return

        lines.append(f"可以胡牌：{win_type}")
        lines.append("")
        lines.extend(self._format_groups(groups))
        lines.append("")
        lines.extend(self._format_fan_info(fan_info))
        self._write_output("\n".join(lines))

    def _calculate_win_check(self):
        self._ensure_no_uncommitted()
        if self.hand_groups:
            raise ValueError("模式2使用未分组手牌；如需使用分组，请切换到模式1")

        hand = self._make_hand(hand_tiles=self.hand_tiles)
        success, groups, win_type, fan_info = self.checker.can_win(hand)

        lines = ["模式2：胡牌判定", ""]
        if not success:
            lines.append("无法胡牌")
            self._write_output("\n".join(lines))
            return

        lines.append(f"可以胡牌：{win_type}")
        lines.append("")
        lines.extend(self._format_groups(groups))
        lines.append("")
        lines.extend(self._format_fan_info(fan_info))
        self._write_output("\n".join(lines))

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
            self._write_output("\n".join(lines))
            return

        visible_tiles = self._visible_tile_values(hand)
        lines.append("听牌：")
        for win_type, info in ready_info.items():
            availability = analyze_ready_tiles(info["tiles"], visible_tiles)
            lines.append(f"【{win_type}】")
            for tile_value in info["tiles"]:
                detail = info["details"][tile_value]
                fan_info = detail.get("fan_info")
                fan_text = self._short_fan_text(fan_info)
                display_tile = availability[tile_value]["display"]
                lines.append(f"  {display_tile}: {fan_text}")
            lines.append("")

        self._write_output("\n".join(lines).rstrip())

    @staticmethod
    def _visible_tile_values(hand):
        values = []
        for group in hand.melded_groups:
            values.extend(tile.value for tile in group.tiles)
        values.extend(tile.value for tile in hand.hand_tiles)
        return values

    def _make_hand(
        self,
        hand_tiles=None,
        hand_groups=None,
        include_melds=True,
    ):
        method = self.winning_method.get() or None
        return Hand(
            melded_groups=list(self.melded_groups) if include_melds else [],
            hand_tiles=[create_tile_from_value(value) for value in (hand_tiles or [])],
            hand_groups=[
                [create_tile_from_value(value) for value in group]
                for group in (hand_groups or [])
            ],
            winning_method=method,
            should_win_in_mode=self.mode.get() in {"1", "2"},
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

        total = fan_info.get("total_fan", 0)
        lines = [
            f"总番: {total}番",
            f"封顶后: {fan_info.get('capped_fan', 0)}番",
            f"应赔付筹码: {fan_info.get('payment', 0)}",
        ]
        if fan_info.get("can_start"):
            lines.append(f"满足起胡条件（{MIN_FAN}番起胡）")
        else:
            lines.append(f"警告: 不满足起胡条件（需要{MIN_FAN}番，当前{total}番）")

        fan_result = fan_info.get("fan_result")
        if fan_result and fan_result.results:
            lines.append("番种明细:")
            for result in fan_result.results:
                lines.append(f"  {result}")
        else:
            lines.append("没有满足的番种")

        if fan_result and fan_result.excluded:
            lines.append("被排除的番种:")
            for fan_type, reason in fan_result.excluded:
                lines.append(f"  {fan_type.fan_name}: {reason}")

        return lines

    def _short_fan_text(self, fan_info):
        if not fan_info:
            return "番数不可用"

        total = fan_info.get("total_fan", 0)
        payment = fan_info.get("payment", 0)
        prefix = f"{total}番，赔付{payment}"
        if not fan_info.get("can_start"):
            prefix += "，不满足1番起胡"

        fan_result = fan_info.get("fan_result")
        if fan_result and fan_result.results:
            names = "、".join(result.fan_type.fan_name for result in fan_result.results)
            return f"{prefix}（{names}）"
        return f"{prefix}（没有满足的番种）"

    def _refresh_all(self):
        self._update_status()
        self._update_tile_buttons()
        self._draw_state()

    def _update_status(self):
        text = (
            f"模式: {self.mode.get()}\n"
            f"手牌区: {len(self.hand_tiles)} 张\n"
            f"当前分组: {len(self.current_group)} 张\n"
            f"已确认分组: {len(self.hand_groups)} 组\n"
            f"当前鸣牌: {len(self.current_meld)} 张\n"
            f"已确认鸣牌: {len(self.melded_groups)} 组"
        )
        self.status_label.configure(text=text)

    def _update_tile_buttons(self):
        for tile_value, button in self.tile_buttons.items():
            used = self._used_count(tile_value)
            limit = TILE_COUNTS[tile_value]
            image = self.button_images.get(tile_value)
            if image:
                button.configure(
                    image=image,
                    text=str(limit - used),
                    compound="top",
                    width=BUTTON_W,
                    height=BUTTON_H,
                    font=("Microsoft YaHei UI", 10, "bold"),
                    state="disabled" if used >= limit else "normal",
                )
            else:
                button.configure(
                    image="",
                    text=f"{tile_value}\n{limit - used}",
                    width=4,
                    height=2,
                    state="disabled" if used >= limit else "normal",
                )

    def _used_count(self, value):
        count = self.hand_tiles.count(value)
        count += self.current_group.count(value)
        count += self.current_meld.count(value)
        for group in self.hand_groups:
            count += group.count(value)
        for meld in self.melded_groups:
            count += sum(1 for tile in meld.tiles if tile.value == value)
        return count

    def _draw_state(self):
        self.canvas.delete("all")
        y = 16
        y = self._draw_section("鸣牌", self.melded_groups, y, is_meld=True)
        y = self._draw_section("已确认分组", self.hand_groups, y, is_group=True)
        y = self._draw_section("手牌区", [self.hand_tiles], y, is_group=True)
        y = self._draw_section("当前分组", [self.current_group], y, is_group=True)
        y = self._draw_section("当前鸣牌", [self.current_meld], y, is_group=True)
        self.canvas.configure(scrollregion=(0, 0, max(self.canvas.winfo_width(), 800), y + 20))

    def _draw_section(self, title, items, y, is_meld=False, is_group=False):
        x = 16
        self.canvas.create_text(x, y, text=title, anchor="nw", font=("Microsoft YaHei UI", 10, "bold"))
        y += 24

        if not items or all(not item for item in items):
            self.canvas.create_text(x, y + 12, text="空", anchor="nw", fill="#81776a")
            return y + 44

        for item in items:
            if is_meld:
                self._draw_meld(x, y, item)
                y += self._row_height() + 14
            elif is_group:
                self._draw_value_group(x, y, item)
                y += self._row_height() + 14
        return y + 8

    def _draw_meld(self, x, y, meld):
        self.canvas.create_text(x, y + self._row_height() + 5, text=meld.group_type, anchor="nw", fill="#5d5348")
        tile_x = x + 64
        exposed = meld.group_type != "暗杠"
        for idx, tile in enumerate(meld.tiles):
            rotated = exposed and idx == len(meld.tiles) - 1
            width, _ = self._tile_size(tile.value, rotated=rotated)
            self._draw_tile(tile_x, y, tile.value, rotated=rotated, concealed=False)
            tile_x += width + TILE_GAP

    def _draw_value_group(self, x, y, values):
        tile_x = x
        for value in values:
            width, _ = self._tile_size(value)
            self._draw_tile(tile_x, y, value)
            tile_x += width + TILE_GAP

    def _draw_tile(self, x, y, value, rotated=False, concealed=False):
        image = self._tile_image(value, rotated=rotated)
        width, height = self._tile_size(value, rotated=rotated)
        fill = "#efe1c8" if not concealed else "#d5c7b1"
        outline = "#7a5d3a" if not rotated else "#a34f3f"
        self.canvas.create_rectangle(x, y, x + width, y + height, fill=fill, outline=outline, width=2)

        if image:
            self.canvas.create_image(x + width / 2, y + height / 2, image=image)
            return

        kwargs = {"text": str(value), "font": ("Microsoft YaHei UI", 12, "bold"), "fill": "#2b2520"}
        if rotated:
            kwargs["angle"] = 90
        self.canvas.create_text(x + width / 2, y + height / 2, **kwargs)

    def _tile_image(self, value, rotated=False):
        if not rotated:
            return self.table_images.get(value)
        return self._rotated_tile_image(value)

    def _tile_size(self, value, rotated=False):
        image = self._tile_image(value, rotated=rotated)
        if image:
            return image.width(), image.height()
        return (TILE_H, TILE_W) if rotated else (TILE_W, TILE_H)

    def _row_height(self):
        heights = [image.height() for image in self.table_images.values()]
        return max(heights, default=TILE_H)

    def _rotated_tile_image(self, value):
        if value in self.rotated_table_images:
            return self.rotated_table_images[value]

        source = self.table_images.get(value)
        if not source:
            return None

        rotated = tk.PhotoImage(width=source.height(), height=source.width())
        for x in range(source.width()):
            for y in range(source.height()):
                rotated.put(self._photo_color(source.get(x, y)), (source.height() - 1 - y, x))

        self.rotated_table_images[value] = rotated
        return rotated

    @staticmethod
    def _photo_color(color):
        if isinstance(color, tuple):
            return "#%02x%02x%02x" % color
        return color

    def _write_output(self, text):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        if text:
            self.output.insert("1.0", text)
        self.output.configure(state="normal")


def main():
    app = MahjongGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
