"""WOS (White Out Survival) 이벤트 계산기

목표 점수까지 필요한 양을 계산한다.
- 탭(Notebook): 이벤트 하나당 탭 하나
- 리스트: 각 이벤트의 점수 행동 목록 (수량 입력 -> 점수 자동 합산)

새 이벤트 추가 = 아래 EVENTS 리스트에 항목 하나 추가하면 끝.
"""
import tkinter as tk
from tkinter import ttk

APP_TITLE = "WOS 이벤트 계산기"

# ---------------------------------------------------------------------------
# 이벤트 데이터 정의
#   name      : 탭 이름
#   items     : 점수 행동 목록 [{name, points(1단위당 점수), unit(표시용 단위)}]
#   milestones: 보상 단계 [{score, reward}]  (점수 오름차순)
# ---------------------------------------------------------------------------
EVENTS = [
    {
        "name": "예시 이벤트",
        "items": [
            {"name": "예: 가속 1분", "points": 10, "unit": "분"},
            {"name": "예: 고기 1만", "points": 5, "unit": "만"},
            {"name": "예: 영웅 경험치 책", "points": 100, "unit": "개"},
        ],
        "milestones": [
            {"score": 1000, "reward": "1단계 보상"},
            {"score": 5000, "reward": "2단계 보상"},
            {"score": 20000, "reward": "최종 보상"},
        ],
    },
]


class EventTab(ttk.Frame):
    """이벤트 하나에 해당하는 탭."""

    def __init__(self, master, event):
        super().__init__(master, padding=12)
        self.event = event
        self.qty_vars = []  # 각 item의 수량 입력 변수

        # --- 점수 행동 리스트 (헤더) ---
        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text="행동", width=22, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="단위당 점수", width=12, font=("Segoe UI", 10, "bold")).grid(row=0, column=1)
        ttk.Label(header, text="보유/계획 수량", width=14, font=("Segoe UI", 10, "bold")).grid(row=0, column=2)
        ttk.Label(header, text="소계", width=12, font=("Segoe UI", 10, "bold")).grid(row=0, column=3)

        ttk.Separator(self).pack(fill="x", pady=4)

        # --- 점수 행동 리스트 (행들) ---
        rows = ttk.Frame(self)
        rows.pack(fill="x")
        self.subtotal_labels = []
        for i, item in enumerate(event["items"]):
            ttk.Label(rows, text=item["name"], width=22).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Label(rows, text=f'{item["points"]:,} 점', width=12, anchor="e").grid(row=i, column=1, padx=4)

            var = tk.StringVar(value="0")
            var.trace_add("write", lambda *a: self.recalc())
            ttk.Entry(rows, textvariable=var, width=14, justify="right").grid(row=i, column=2, padx=4)
            self.qty_vars.append(var)

            sub = ttk.Label(rows, text="0 점", width=12, anchor="e")
            sub.grid(row=i, column=3, padx=4)
            self.subtotal_labels.append(sub)

        ttk.Separator(self).pack(fill="x", pady=8)

        # --- 목표 점수 입력 ---
        target_row = ttk.Frame(self)
        target_row.pack(fill="x")
        ttk.Label(target_row, text="목표 점수:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.target_var = tk.StringVar(value="")
        self.target_var.trace_add("write", lambda *a: self.recalc())
        ttk.Entry(target_row, textvariable=self.target_var, width=14, justify="right").pack(side="left", padx=6)

        # --- 결과 표시 ---
        self.result = ttk.Label(self, text="", font=("Segoe UI", 11), justify="left", foreground="#1a5fb4")
        self.result.pack(anchor="w", pady=(10, 0))

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

        # 보상 단계 현황
        for m in self.event["milestones"]:
            if total >= m["score"]:
                mark = "✅"
            else:
                mark = f"❌ ({int(m['score'] - total):,} 점 부족)"
            lines.append(f"  {m['score']:,}점 [{m['reward']}] {mark}")

        self.result.config(text="\n".join(lines))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("560x520")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        for event in EVENTS:
            nb.add(EventTab(nb, event), text=event["name"])


if __name__ == "__main__":
    App().mainloop()
