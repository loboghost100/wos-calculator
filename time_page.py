"""시간 페이지: 현재 PC 시간 기준 등록 시각까지 남은 시간."""
import tkinter as tk
from tkinter import ttk
from datetime import datetime

from config import BASE_TIME


class TimePage(ttk.Frame):
    """현재 PC 시간을 기준으로 등록된 시각과의 차이를 보여준다.

    - 기본값 AM 9:00은 코드 고정(삭제 불가)
    - 사용자가 시각 추가/삭제 가능 (userdata에 저장)
    - 12h / 24h 표시 전환 (내부 표현은 0~1439분으로 형식 무관)
    """

    def __init__(self, master, store):
        super().__init__(master, padding=14)
        self.store = store
        self.fmt = store.get("_time_format", "24h")
        self.user_times = sorted(set(store.get("_user_times", [])))
        self.rows = []          # [(target_min, diff_label)]
        self._after_id = None

        ttk.Label(self, text="시간", font=("Segoe UI", 14, "bold")).pack(anchor="w")

        # 현재 시간 + 형식 토글
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(6, 4))
        self.now_label = ttk.Label(top, text="", font=("Segoe UI", 11))
        self.now_label.pack(side="left")

        fmt_box = ttk.Frame(top)
        fmt_box.pack(side="right")
        ttk.Label(fmt_box, text="표시: ").pack(side="left")
        self.fmt_var = tk.StringVar(value=self.fmt)
        ttk.Radiobutton(fmt_box, text="24h", value="24h", variable=self.fmt_var,
                        command=self._on_format).pack(side="left")
        ttk.Radiobutton(fmt_box, text="12h", value="12h", variable=self.fmt_var,
                        command=self._on_format).pack(side="left")

        ttk.Separator(self).pack(fill="x", pady=6)

        # 시각 목록
        self.list_frame = ttk.Frame(self)
        self.list_frame.pack(fill="x")

        ttk.Separator(self).pack(fill="x", pady=8)

        # 시각 추가 컨트롤
        add = ttk.Frame(self)
        add.pack(fill="x")
        ttk.Label(add, text="시각 추가:").pack(side="left")
        self.add_hour = ttk.Spinbox(add, width=4, justify="right")
        self.add_hour.set("9")
        self.add_hour.pack(side="left", padx=(6, 0))
        ttk.Label(add, text=":").pack(side="left", padx=2)
        self.add_min = ttk.Spinbox(add, width=4, from_=0, to=59, justify="right")
        self.add_min.set("00")
        self.add_min.pack(side="left")
        self.add_period = ttk.Combobox(add, width=4, values=["AM", "PM"], state="readonly")
        self.add_period.current(0)
        self.add_period.pack(side="left", padx=6)
        ttk.Button(add, text="추가", command=self._add).pack(side="left", padx=4)

        self.msg = ttk.Label(self, text="", foreground="#c01c28")
        self.msg.pack(anchor="w", pady=(4, 0))

        self._sync_add_controls()
        self._render_list()
        self._tick()

    # --- 시각 표현 ---
    def _fmt_time(self, minutes):
        h, m = divmod(minutes % (24 * 60), 60)
        if self.fmt == "12h":
            period = "AM" if h < 12 else "PM"
            h12 = h % 12 or 12
            return f"{period} {h12}:{m:02d}"
        return f"{h:02d}:{m:02d}"

    def _diff_text(self, target, now_min):
        # 목표 시각은 항상 미래 -> 다음 발생까지 남은 시간 (오늘 지났으면 내일)
        diff = (target - now_min) % (24 * 60)
        if diff == 0:
            return "지금"
        h, m = divmod(diff, 60)
        return f"{h}시간 {m}분 남음"

    # --- 추가/삭제 ---
    def _parse_add(self):
        try:
            h = int(self.add_hour.get())
            m = int(self.add_min.get() or 0)
        except (ValueError, TypeError):
            return None
        if not (0 <= m <= 59):
            return None
        if self.fmt == "12h":
            if not (1 <= h <= 12):
                return None
            if self.add_period.get() == "AM":
                h = 0 if h == 12 else h
            else:
                h = 12 if h == 12 else h + 12
        elif not (0 <= h <= 23):
            return None
        return h * 60 + m

    def _add(self):
        mins = self._parse_add()
        if mins is None:
            self.msg.config(text="시각 형식이 올바르지 않습니다.")
            return
        if mins == BASE_TIME or mins in self.user_times:
            self.msg.config(text="이미 등록된 시각입니다.")
            return
        self.user_times = sorted(set(self.user_times) | {mins})
        self.store.set("_user_times", self.user_times)
        self.msg.config(text="")
        self._render_list()

    def _delete(self, mins):
        if mins in self.user_times:
            self.user_times.remove(mins)
            self.store.set("_user_times", self.user_times)
            self._render_list()

    # --- 형식 토글 ---
    def _on_format(self):
        self.fmt = self.fmt_var.get()
        self.store.set("_time_format", self.fmt)
        self._sync_add_controls()
        self._render_list()

    def _sync_add_controls(self):
        if self.fmt == "12h":
            self.add_hour.config(from_=1, to=12)
            self.add_period.configure(state="readonly")
        else:
            self.add_hour.config(from_=0, to=23)
            self.add_period.configure(state="disabled")

    # --- 목록 렌더링 + 라이브 갱신 ---
    def _render_list(self):
        for c in self.list_frame.winfo_children():
            c.destroy()
        self.rows = []
        # 기본값 포함 전체를 시각 순으로 정렬
        all_times = sorted(set(self.user_times) | {BASE_TIME})
        entries = [(t, t == BASE_TIME) for t in all_times]
        for target, is_base in entries:
            row = ttk.Frame(self.list_frame)
            row.pack(fill="x", pady=2)
            name = self._fmt_time(target) + ("  (기본)" if is_base else "")
            ttk.Label(row, text=name, width=16, font=("Segoe UI", 11)).pack(side="left")
            diff_lbl = ttk.Label(row, text="", font=("Segoe UI", 11), foreground="#1a5fb4")
            diff_lbl.pack(side="left", padx=8)
            self.rows.append((target, diff_lbl))
            if not is_base:
                ttk.Button(row, text="삭제", width=5,
                           command=lambda t=target: self._delete(t)).pack(side="right")
        self._refresh_diffs()

    def _refresh_diffs(self):
        now = datetime.now()
        now_min = now.hour * 60 + now.minute
        for target, lbl in self.rows:
            lbl.config(text=self._diff_text(target, now_min))

    def _tick(self):
        now = datetime.now()
        if self.fmt == "12h":
            period = "AM" if now.hour < 12 else "PM"
            h12 = now.hour % 12 or 12
            now_str = f"{period} {h12}:{now.minute:02d}"
        else:
            now_str = f"{now.hour:02d}:{now.minute:02d}"
        self.now_label.config(text="현재 시간: " + now_str)
        self._refresh_diffs()
        self._after_id = self.after(1000, self._tick)

    def destroy(self):
        if self._after_id:
            self.after_cancel(self._after_id)
        super().destroy()
