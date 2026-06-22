"""여러 날(예: 연맹 대작전 6일)을 한 페이지에서 다루는 계산기.

상단에 타이틀+보상 아이콘을 한 번 그리고, 그 아래 날짜 탭 버튼을 둔다.
탭을 누르면 해당 날짜의 본문(EventCalc, 헤더 없는 형태)이 표시된다.
각 날짜는 독립된 현재/목표 점수·배점을 가지며, "<이벤트키>::<날짜라벨>" 키로 저장된다.
"""
import tkinter as tk
from tkinter import ttk

from resources import resource, is_number, to_num
from event_calc import EventCalc


class MultiDayEventCalc(ttk.Frame):
    def __init__(self, master, event, store):
        super().__init__(master, padding=14)
        self.event = event
        self.store = store
        self.base_key = event["_key"]

        # --- 타이틀 + 보상 아이콘 (페이지에 한 번만) ---
        header = ttk.Frame(self)
        header.pack(fill="x", anchor="w")
        ttk.Label(header, text=event["name"], font=("Segoe UI", 14, "bold")).pack(side="left")
        self._reward_imgs = []  # GC 방지용 참조 보관
        for j, icon in enumerate(event.get("rewards", [])):
            try:
                img = tk.PhotoImage(file=resource("assets", icon))
            except Exception:
                continue
            self._reward_imgs.append(img)
            ttk.Label(header, image=img).pack(side="left", padx=(12 if j == 0 else 4, 0))

        # --- 배점 보너스 % (페이지 공통: 모든 날짜에 동일 적용) ---
        # 저장은 기본 배점(보너스 미반영)으로 하고, 여기 입력한 %만큼 실효 배점을 올려서 보여준다.
        bonus_row = ttk.Frame(self)
        bonus_row.pack(fill="x", pady=(8, 0))
        ttk.Label(bonus_row, text="배점 보너스:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.bonus_var = tk.StringVar(value=store.event(self.base_key).get("bonus_pct", "0"))
        vcmd = (self.register(is_number), "%P")
        ttk.Entry(bonus_row, textvariable=self.bonus_var, width=6, justify="right",
                  validate="key", validatecommand=vcmd).pack(side="left", padx=(4, 2))
        ttk.Label(bonus_row, text="%  (전문가 보너스 등 추가 배점)").pack(side="left")
        self.bonus_var.trace_add("write", lambda *a: self._on_bonus_change())

        # --- 날짜 탭 버튼 ---
        tabs = ttk.Frame(self)
        tabs.pack(fill="x", pady=(8, 0))
        self.tab_btns = {}
        for day in event["days"]:
            label = day["label"]
            btn = ttk.Button(tabs, text=label, width=6,
                             command=lambda d=day: self.show_day(d))
            btn.pack(side="left", padx=(0, 4))
            self.tab_btns[label] = btn

        ttk.Separator(self).pack(fill="x", pady=8)

        # --- 날짜 본문 영역 (lazy 생성, 상태 유지) ---
        self.body_area = ttk.Frame(self)
        self.body_area.pack(fill="both", expand=True)
        self.bodies = {}
        self.active_label = None

        self.show_day(event["days"][0])

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
            self.bodies[label] = EventCalc(
                self.body_area, pseudo, self.store, show_header=False,
                bonus_getter=self._mult, points_editable=False)
        self.bodies[label].pack(fill="both", expand=True)

        # 선택된 탭 강조
        for lbl, btn in self.tab_btns.items():
            btn.state(["pressed"] if lbl == label else ["!pressed"])
        self.active_label = label

    def _mult(self):
        """현재 배점 배율. 예: 50% -> 1.5 (빈칸/0% -> 1.0)."""
        return 1 + to_num(self.bonus_var.get()) / 100

    def _on_bonus_change(self):
        # % 저장 (이벤트 단위 공통) + 생성된 모든 날짜 본문 재계산
        rec = self.store.event(self.base_key)
        rec["bonus_pct"] = self.bonus_var.get()
        self.store.schedule_save()
        for body in self.bodies.values():
            body.recalc()
