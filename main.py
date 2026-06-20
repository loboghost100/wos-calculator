"""WOS (White Out Survival) 이벤트 계산기

목표 점수까지 필요한 양을 계산한다.
- 왼쪽: 트리 사이드바 (그룹 -> 하위 이벤트, 펼침/접힘)
- 오른쪽: 선택한 이벤트의 계산기 (수량 입력 -> 점수 자동 합산)

새 이벤트 추가 = 아래 EVENT_GROUPS 데이터에 항목 추가하면 끝.
"""
import tkinter as tk
from tkinter import ttk

APP_TITLE = "WOS 이벤트 계산기"

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
        "events": [_placeholder("(이벤트 추가 예정)")],
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


class EventCalc(ttk.Frame):
    """이벤트 하나의 계산기 화면 (오른쪽 패널에 표시)."""

    def __init__(self, master, event):
        super().__init__(master, padding=14)
        self.event = event
        self.qty_vars = []

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

            var = tk.StringVar(value="0")
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
        self.target_var = tk.StringVar(value="")
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
        self.active_btn = None       # 현재 선택된 이벤트 버튼
        self.first_event = None      # (버튼, 이벤트) 자동 선택용

        for group in EVENT_GROUPS:
            self._add_group(group)

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
        btn.config(command=lambda: self._select(btn, event))
        self._hover(btn, SUB_BG, SUB_HOVER)
        btn.pack(fill="x")
        if self.first_event is None:
            self.first_event = (btn, event)

    def _hover(self, btn, normal, hover):
        # 선택된 버튼은 호버 색을 덮어쓰지 않도록 처리
        btn.bind("<Enter>", lambda e: btn.config(bg=hover) if btn is not self.active_btn else None)
        btn.bind("<Leave>", lambda e: btn.config(bg=normal) if btn is not self.active_btn else None)

    def _select(self, btn, event):
        if self.active_btn is not None:
            self.active_btn.config(bg=SUB_BG)
        self.active_btn = btn
        btn.config(bg=SUB_ACTIVE)
        self.on_event_select(event)

    def select_first(self):
        if self.first_event:
            btn, event = self.first_event
            self._select(btn, event)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("740x540")

        # --- 왼쪽: 버튼형 사이드바 ---
        self.sidebar = Sidebar(self, self.show_event)
        self.sidebar.pack(side="left", fill="y")

        # --- 오른쪽: 계산기 표시 영역 ---
        self.right = ttk.Frame(self)
        self.right.pack(side="left", fill="both", expand=True)

        self.calcs = {}  # event id -> EventCalc (lazy 생성, 상태 유지)
        self.sidebar.select_first()

    def show_event(self, event):
        key = id(event)
        for child in self.right.winfo_children():
            child.pack_forget()
        if key not in self.calcs:
            self.calcs[key] = EventCalc(self.right, event)
        self.calcs[key].pack(fill="both", expand=True)


if __name__ == "__main__":
    App().mainloop()
