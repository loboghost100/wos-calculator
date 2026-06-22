"""여러 날(예: 연맹 대작전 6일)을 한 페이지에서 다루는 계산기.

상단에 타이틀+보상 아이콘을 한 번 그리고, 그 아래 날짜 탭 버튼을 둔다.
탭을 누르면 해당 날짜의 본문(헤더 없는 형태)이 표시된다.
각 날짜는 독립된 현재/목표 점수·항목을 가지며, "<이벤트키>::<날짜라벨>" 키로 저장된다.

event 옵션:
- bonus=True   : '전문가의 도움'(배점 보너스 %) 입력칸 (연맹 대작전)
- editable=True: 각 날짜를 보기/편집 토글로 유저가 직접 관리
- dynamic=True : 탭 개수를 유저가 숫자로 지정 (1,2,3,… 라벨), 개수는 저장됨
"""
import tkinter as tk
from tkinter import ttk

from resources import resource, is_number, to_num
from event_calc import EventCalc
from editable_calc import EditableCalc


def _roman(n):
    """1 -> 'I', 2 -> 'II' … (탭 라벨용)."""
    table = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
             (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
             (5, "V"), (4, "IV"), (1, "I")]
    out = []
    for v, s in table:
        while n >= v:
            out.append(s)
            n -= v
    return "".join(out)


class MultiDayEventCalc(ttk.Frame):
    def __init__(self, master, event, store):
        super().__init__(master, padding=14)
        self.event = event
        self.store = store
        self.base_key = event["_key"]
        self.dynamic = event.get("dynamic", False)
        self.bodies = {}
        self.active_label = None

        # --- 타이틀 + 보상 아이콘 (페이지에 한 번만) ---
        header = ttk.Frame(self)
        header.pack(fill="x", anchor="w")
        ttk.Label(header, text=event["name"], font=("Segoe UI", 14, "bold")).pack(side="left")
        if event.get("dynamic"):
            # Custom(동적) 페이지: 이름 옆 유저 제목 입력칸
            self.title_var = tk.StringVar(value=store.event(self.base_key).get("title", ""))
            self.title_var.trace_add("write", lambda *a: self._save_title())
            ttk.Entry(header, textvariable=self.title_var, width=24,
                      font=("Segoe UI", 12)).pack(side="left", padx=(10, 0))
        self._reward_imgs = []  # GC 방지용 참조 보관
        for j, icon in enumerate(event.get("rewards", [])):
            try:
                img = tk.PhotoImage(file=resource("assets", icon))
            except Exception:
                continue
            self._reward_imgs.append(img)
            ttk.Label(header, image=img).pack(side="left", padx=(12 if j == 0 else 4, 0))

        # --- 탭 줄: (왼쪽) 탭 버튼들  (오른쪽) 보너스% 또는 탭 개수 입력 ---
        tabs = ttk.Frame(self)
        tabs.pack(fill="x", pady=(8, 0))
        self.tab_bar = ttk.Frame(tabs)
        self.tab_bar.pack(side="left")
        self.tab_btns = {}

        # 배점 보너스 %: bonus 플래그가 있는 이벤트(연맹 대작전)에만 표시.
        self.bonus_getter = None
        if event.get("bonus"):
            self.bonus_var = tk.StringVar(value=store.event(self.base_key).get("bonus_pct", "0"))
            vcmd = (self.register(is_number), "%P")
            ttk.Label(tabs, text="%").pack(side="right", padx=(2, 0))
            ttk.Entry(tabs, textvariable=self.bonus_var, width=5, justify="right",
                      validate="key", validatecommand=vcmd).pack(side="right", padx=(4, 0))
            ttk.Label(tabs, text="전문가의 도움", font=("Segoe UI", 10, "bold")).pack(side="right", padx=(12, 0))
            self.bonus_var.trace_add("write", lambda *a: self._on_bonus_change())
            self.bonus_getter = self._mult

        # 탭 개수 조절: dynamic 이벤트(연맹 Custom)에만. [−] N [+] (− 왼쪽, + 오른쪽)
        if self.dynamic:
            self.day_count = self._saved_count()
            ctrl = ttk.Frame(tabs)
            ctrl.pack(side="right")
            ttk.Label(ctrl, text="탭 개수", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 8))
            ttk.Button(ctrl, text="−", width=2, command=lambda: self._step(-1)).pack(side="left")
            self.count_label = ttk.Label(ctrl, text=str(self.day_count), width=3, anchor="center")
            self.count_label.pack(side="left", padx=2)
            ttk.Button(ctrl, text="+", width=2, command=lambda: self._step(1)).pack(side="left")

        ttk.Separator(self).pack(fill="x", pady=8)

        # --- 날짜 본문 영역 (lazy 생성, 상태 유지) ---
        self.body_area = ttk.Frame(self)
        self.body_area.pack(fill="both", expand=True)

        self.days = self._make_days()
        self._rebuild_tabs()

    # --- 탭/날짜 구성 ---
    def _saved_count(self):
        try:
            return max(1, int(self.store.event(self.base_key).get("day_count", 1)))
        except (ValueError, TypeError):
            return 1

    def _make_days(self):
        if self.dynamic:
            n = self._saved_count()
            return [{"label": _roman(i), "items": []} for i in range(1, n + 1)]
        return self.event["days"]

    def _rebuild_tabs(self):
        for b in self.tab_bar.winfo_children():
            b.destroy()
        self.tab_btns = {}
        for day in self.days:
            label = day["label"]
            btn = ttk.Button(self.tab_bar, text=label, width=6,
                             command=lambda d=day: self.show_day(d))
            btn.pack(side="left", padx=(0, 4))
            self.tab_btns[label] = btn

        # 보던 탭 유지, 없으면 첫 탭
        target = None
        if self.active_label in self.tab_btns:
            target = next(d for d in self.days if d["label"] == self.active_label)
        elif self.days:
            target = self.days[0]
        if target:
            self.show_day(target)

    def _step(self, delta):
        n = max(1, min(60, self.day_count + delta))
        if n == self.day_count:
            return
        self.day_count = n
        rec = self.store.event(self.base_key)
        rec["day_count"] = str(n)
        self.store.schedule_save()
        self.count_label.config(text=str(n))
        self.days = [{"label": _roman(i), "items": []} for i in range(1, n + 1)]
        self._rebuild_tabs()

    def show_day(self, day):
        label = day["label"]
        for child in self.body_area.winfo_children():
            child.pack_forget()
        if label not in self.bodies:
            pseudo = {
                "name": f'{self.event["name"]} {label}',
                "items": day["items"],
                "rewards": [],
                "defaults": day.get("defaults", {}),
                "_key": f"{self.base_key}::{label}",
            }
            if self.event.get("editable"):
                self.bodies[label] = EditableCalc(
                    self.body_area, pseudo, self.store, show_header=False)
            else:
                self.bodies[label] = EventCalc(
                    self.body_area, pseudo, self.store, show_header=False,
                    bonus_getter=self.bonus_getter, points_editable=False)
        self.bodies[label].pack(fill="both", expand=True)

        for lbl, btn in self.tab_btns.items():
            btn.state(["pressed"] if lbl == label else ["!pressed"])
        self.active_label = label

    # --- 보너스 ---
    def _mult(self):
        """현재 배점 배율. 예: 50% -> 1.5 (빈칸/0% -> 1.0)."""
        return 1 + to_num(self.bonus_var.get()) / 100

    def _on_bonus_change(self):
        rec = self.store.event(self.base_key)
        rec["bonus_pct"] = self.bonus_var.get()
        self.store.schedule_save()
        for body in self.bodies.values():
            body.recalc()

    def _save_title(self):
        rec = self.store.event(self.base_key)
        rec["title"] = self.title_var.get()
        self.store.schedule_save()
