"""여러 날(예: 연맹 대작전 6일)을 한 페이지에서 다루는 계산기.

상단에 타이틀+보상 아이콘을 한 번 그리고, 그 아래 날짜 탭 버튼을 둔다.
탭을 누르면 해당 날짜의 본문(EventCalc, 헤더 없는 형태)이 표시된다.
각 날짜는 독립된 현재/목표 점수·배점을 가지며, "<이벤트키>::<날짜라벨>" 키로 저장된다.
"""
import tkinter as tk
from tkinter import ttk

from resources import resource
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
            self.bodies[label] = EventCalc(self.body_area, pseudo, self.store, show_header=False)
        self.bodies[label].pack(fill="both", expand=True)

        # 선택된 탭 강조
        for lbl, btn in self.tab_btns.items():
            btn.state(["pressed"] if lbl == label else ["!pressed"])
        self.active_label = label
