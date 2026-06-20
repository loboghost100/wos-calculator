"""WOS (White Out Survival) 이벤트 계산기

목표 점수까지 필요한 양을 계산한다.
- 왼쪽: 트리 사이드바 (그룹 -> 하위 이벤트, 펼침/접힘)
- 오른쪽: 선택한 이벤트의 계산기 (수량 입력 -> 점수 자동 합산)

새 이벤트 추가 = 아래 EVENT_GROUPS 데이터에 항목 추가하면 끝.
"""
import os
import sys
import json
import tkinter as tk
from tkinter import ttk

APP_TITLE = "WOS 이벤트 계산기"


# ---------------------------------------------------------------------------
# 사용자 데이터 저장소 (JSON)
#   저장 위치: 실행 파일(.exe)과 같은 폴더의 userdata.json
#   (개발 중 .py 실행 시에는 스크립트와 같은 폴더)
# ---------------------------------------------------------------------------
def _data_file():
    if getattr(sys, "frozen", False):       # PyInstaller로 빌드된 .exe
        base = os.path.dirname(sys.executable)
    else:                                   # 일반 .py 실행
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "userdata.json")


class Store:
    """사용자 입력값을 JSON으로 저장/복원."""

    def __init__(self):
        self.path = _data_file()
        self.data = self._load()
        self._root = None       # debounce용 after 스케줄러
        self._pending = None

    def attach(self, root):
        self._root = root

    def event(self, key):
        return self.data.setdefault(key, {"target": "", "items": {}})

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def save(self):
        self._pending = None
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def schedule_save(self):
        # 입력 중엔 매 타이핑마다 쓰지 않고 0.4초 뒤 한 번만 저장
        if self._root is None:
            self.save()
            return
        if self._pending:
            self._root.after_cancel(self._pending)
        self._pending = self._root.after(400, self.save)

# ---------------------------------------------------------------------------
# 이벤트 데이터 정의 (그룹 -> 이벤트)
#   group.name        : 사이드바 상위 항목(펼쳐지는 그룹)
#   event.name        : 하위 항목(클릭 시 오른쪽에 계산기 표시)
#   event.items       : 점수 행동 [{name, points(1단위당 점수), unit}]
#   event.milestones  : 보상 단계 [{score, reward}] (점수 오름차순)
# ---------------------------------------------------------------------------
def _placeholder(name):
    """아직 내용 미정인 자리표시용 이벤트."""
    return {
        "name": name,
        "items": [{"name": "(행동 미정)", "points": 0, "unit": ""}],
        "milestones": [],
    }


EVENT_GROUPS = [
    {
        "name": "시간",
        "events": [],  # 이벤트가 아닌 별개 기능 -> 하위 항목 없이 단독 버튼
    },
    {
        "name": "개인 이벤트",
        "events": [_placeholder("(이벤트 추가 예정)")],
    },
    {
        "name": "연맹 이벤트",
        "events": [_placeholder("(이벤트 추가 예정)")],
    },
]

# 저장/복원용 안정적인 키 부여 ("그룹명::이벤트명")
for _group in EVENT_GROUPS:
    for _event in _group["events"]:
        _event["_key"] = f'{_group["name"]}::{_event["name"]}'


class EventCalc(ttk.Frame):
    """이벤트 하나의 계산기 화면 (오른쪽 패널에 표시)."""

    def __init__(self, master, event, store):
        super().__init__(master, padding=14)
        self.event = event
        self.store = store
        self.key = event["_key"]
        self.qty_vars = []
        saved = store.event(self.key)
        saved_items = saved.get("items", {})

        ttk.Label(self, text=event["name"], font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Separator(self).pack(fill="x", pady=8)

        # --- 점수 행동 리스트 (헤더) ---
        rows = ttk.Frame(self)
        rows.pack(fill="x")
        ttk.Label(rows, text="행동", width=20, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(rows, text="단위당 점수", width=11, font=("Segoe UI", 10, "bold")).grid(row=0, column=1)
        ttk.Label(rows, text="수량", width=12, font=("Segoe UI", 10, "bold")).grid(row=0, column=2)
        ttk.Label(rows, text="소계", width=11, font=("Segoe UI", 10, "bold")).grid(row=0, column=3)

        # --- 점수 행동 리스트 (행들) ---
        self.subtotal_labels = []
        for i, item in enumerate(event["items"], start=1):
            ttk.Label(rows, text=item["name"], width=20).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Label(rows, text=f'{item["points"]:,} 점', width=11, anchor="e").grid(row=i, column=1, padx=4)

            var = tk.StringVar(value=saved_items.get(item["name"], "0"))
            var.trace_add("write", lambda *a: self.recalc())
            ttk.Entry(rows, textvariable=var, width=12, justify="right").grid(row=i, column=2, padx=4)
            self.qty_vars.append(var)

            sub = ttk.Label(rows, text="0 점", width=11, anchor="e")
            sub.grid(row=i, column=3, padx=4)
            self.subtotal_labels.append(sub)

        ttk.Separator(self).pack(fill="x", pady=10)

        # --- 목표 점수 입력 ---
        target_row = ttk.Frame(self)
        target_row.pack(fill="x")
        ttk.Label(target_row, text="목표 점수:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.target_var = tk.StringVar(value=saved.get("target", ""))
        self.target_var.trace_add("write", lambda *a: self.recalc())
        ttk.Entry(target_row, textvariable=self.target_var, width=14, justify="right").pack(side="left", padx=6)

        # --- 결과 표시 ---
        self.result = ttk.Label(self, text="", font=("Segoe UI", 11), justify="left", foreground="#1a5fb4")
        self.result.pack(anchor="w", pady=(12, 0))

        self.recalc()

    @staticmethod
    def _to_num(s):
        try:
            return float(s.replace(",", "").strip() or 0)
        except ValueError:
            return 0

    def recalc(self):
        total = 0
        for item, var, lbl in zip(self.event["items"], self.qty_vars, self.subtotal_labels):
            sub = self._to_num(var.get()) * item["points"]
            total += sub
            lbl.config(text=f"{int(sub):,} 점")

        lines = [f"현재 총점: {int(total):,} 점"]

        target = self._to_num(self.target_var.get())
        if target > 0:
            remain = target - total
            if remain > 0:
                lines.append(f"목표까지: {int(remain):,} 점 부족")
            else:
                lines.append(f"목표 달성! (+{int(-remain):,} 점 초과)")

        for m in self.event["milestones"]:
            mark = "✅" if total >= m["score"] else f"❌ ({int(m['score'] - total):,} 점 부족)"
            lines.append(f"  {m['score']:,}점 [{m['reward']}] {mark}")

        self.result.config(text="\n".join(lines))

        # 입력값 저장소에 반영 + 지연 저장
        rec = self.store.event(self.key)
        rec["target"] = self.target_var.get()
        rec["items"] = {item["name"]: var.get()
                        for item, var in zip(self.event["items"], self.qty_vars)}
        self.store.schedule_save()


# 사이드바 색상 테마
SIDEBAR_BG = "#2c3e50"      # 사이드바 배경
GROUP_BG = "#34495e"        # 그룹 버튼
GROUP_HOVER = "#3d566e"
SUB_BG = "#2c3e50"          # 하위 이벤트 버튼
SUB_HOVER = "#3d566e"
SUB_ACTIVE = "#1a5fb4"      # 선택된 이벤트
FG = "#ecf0f1"


class Sidebar(tk.Frame):
    """버튼 느낌의 아코디언 사이드바."""

    def __init__(self, master, on_event_select):
        super().__init__(master, bg=SIDEBAR_BG, width=200)
        self.pack_propagate(False)
        self.on_event_select = on_event_select
        self.active_btn = None       # 현재 선택된 버튼
        self.first = None            # (버튼, payload) 자동 선택용

        for group in EVENT_GROUPS:
            if group["events"]:
                self._add_group(group)
            else:
                self._add_standalone(group)

    def _add_standalone(self, group):
        # 하위 항목 없는 단독 항목 (이벤트가 아닌 별개 기능)
        payload = {"name": group["name"], "page": "standalone"}
        btn = tk.Button(
            self, text=f"  {group['name']}", anchor="w",
            bg=GROUP_BG, fg=FG, font=("Segoe UI", 11, "bold"),
            relief="flat", bd=0, padx=10, pady=10, cursor="hand2",
            activebackground=GROUP_HOVER, activeforeground=FG,
        )
        self._make_selectable(btn, GROUP_BG, GROUP_HOVER, payload)
        btn.pack(fill="x")

    def _add_group(self, group):
        # 펼침 상태와 하위 버튼들을 담을 컨테이너
        state = {"open": True}
        sub_frame = tk.Frame(self, bg=SIDEBAR_BG)

        header = tk.Button(
            self, text=f"  ▾  {group['name']}", anchor="w",
            bg=GROUP_BG, fg=FG, font=("Segoe UI", 11, "bold"),
            relief="flat", bd=0, padx=10, pady=10, cursor="hand2",
            activebackground=GROUP_HOVER, activeforeground=FG,
        )

        def toggle():
            state["open"] = not state["open"]
            header.config(text=f"  {'▾' if state['open'] else '▸'}  {group['name']}")
            if state["open"]:
                sub_frame.pack(fill="x", after=header)
            else:
                sub_frame.pack_forget()

        header.config(command=toggle)
        self._hover(header, GROUP_BG, GROUP_HOVER)
        header.pack(fill="x")
        sub_frame.pack(fill="x")

        for event in group["events"]:
            self._add_event(sub_frame, event)

    def _add_event(self, parent, event):
        btn = tk.Button(
            parent, text=f"      {event['name']}", anchor="w",
            bg=SUB_BG, fg=FG, font=("Segoe UI", 10),
            relief="flat", bd=0, padx=10, pady=8, cursor="hand2",
            activebackground=SUB_HOVER, activeforeground=FG,
        )
        self._make_selectable(btn, SUB_BG, SUB_HOVER, event)
        btn.pack(fill="x")

    def _make_selectable(self, btn, normal, hover, payload):
        btn._normal_bg = normal
        btn._hover_bg = hover
        btn.config(command=lambda: self._select(btn, payload))
        self._hover(btn, normal, hover)
        if self.first is None:
            self.first = (btn, payload)

    def _hover(self, btn, normal, hover):
        # 선택된 버튼은 호버 색을 덮어쓰지 않도록 처리
        btn.bind("<Enter>", lambda e: btn.config(bg=hover) if btn is not self.active_btn else None)
        btn.bind("<Leave>", lambda e: btn.config(bg=normal) if btn is not self.active_btn else None)

    def _select(self, btn, payload):
        if self.active_btn is not None:
            self.active_btn.config(bg=getattr(self.active_btn, "_normal_bg", SUB_BG))
        self.active_btn = btn
        btn.config(bg=SUB_ACTIVE)
        self.on_event_select(payload)

    def select_first(self):
        if self.first:
            btn, payload = self.first
            self._select(btn, payload)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("740x540")

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

        self.calcs = {}  # event id -> EventCalc (lazy 생성, 상태 유지)
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
                self.calcs[key] = self._make_placeholder_page(payload["name"])
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
