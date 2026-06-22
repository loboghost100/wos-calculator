"""WOS (White Out Survival) 이벤트 계산기 — 진입점.

구조:
- config.py      : 상수 + 이벤트 데이터(EVENT_GROUPS)
- resources.py   : 경로/입력 검증 등 공용 헬퍼
- store.py       : 사용자 데이터 저장소(JSON)
- sidebar.py     : 좌측 버튼형 사이드바
- event_calc.py  : 일반 이벤트 계산기(군비/사관)
- custom_calc.py : 커스텀 이벤트 계산기
- time_page.py   : 시간 페이지
"""
import tkinter as tk
from tkinter import ttk

from config import APP_TITLE
from resources import resource
from store import Store
from sidebar import Sidebar
from event_calc import EventCalc
from editable_calc import EditableCalc
from multiday_calc import MultiDayEventCalc
from training_calc import TrainingCalc
from time_page import TimePage


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("780x640")
        try:
            self.iconbitmap(resource("assets", "icon.ico"))
        except Exception:
            pass

        # 사용자 데이터 저장소 (종료 후 재실행해도 입력값 복원)
        self.store = Store()
        self.store.attach(self)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # --- 왼쪽: 버튼형 사이드바 ---
        self.sidebar = Sidebar(self, self.show_event)
        self.sidebar.pack(side="left", fill="y")

        # --- 오른쪽: 계산기 표시 영역 ---
        self.right = ttk.Frame(self)
        self.right.pack(side="left", fill="both", expand=True)

        self.calcs = {}  # payload id -> 위젯 (lazy 생성, 상태 유지)
        self.sidebar.select_first()

    def _on_close(self):
        self.store.save()
        self.destroy()

    def show_event(self, payload):
        key = id(payload)
        for child in self.right.winfo_children():
            child.pack_forget()
        if key not in self.calcs:
            if payload.get("page") == "standalone":
                if payload["name"] == "시간":
                    self.calcs[key] = TimePage(self.right, self.store)
                else:
                    self.calcs[key] = self._make_placeholder_page(payload["name"])
            elif payload.get("training"):
                self.calcs[key] = TrainingCalc(self.right, payload, self.store)
            elif "days" in payload:
                self.calcs[key] = MultiDayEventCalc(self.right, payload, self.store)
            elif payload.get("custom") or payload.get("editable"):
                self.calcs[key] = EditableCalc(self.right, payload, self.store)
            else:
                self.calcs[key] = EventCalc(self.right, payload, self.store)
        self.calcs[key].pack(fill="both", expand=True)

    def _make_placeholder_page(self, name):
        frame = ttk.Frame(self.right, padding=14)
        ttk.Label(frame, text=name, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Separator(frame).pack(fill="x", pady=8)
        ttk.Label(
            frame, text="(이벤트 외 기능 — 내용 준비 중)",
            font=("Segoe UI", 11), foreground="gray",
        ).pack(anchor="w")
        return frame


if __name__ == "__main__":
    App().mainloop()
