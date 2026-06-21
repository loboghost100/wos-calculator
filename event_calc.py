"""일반 이벤트 점수 계산기 (군비/사관 등)."""
import math
import tkinter as tk
from tkinter import ttk

from resources import resource, is_number, comma_format, to_num
from config import item_col_minsize


class EventCalc(ttk.Frame):
    """이벤트 점수 계산기.

    현재 점수 / 목표 점수를 입력하면, 부족한 점수를 채우기 위해 각 항목을
    몇 개 써야 하는지 계산해서 보여준다. 배점은 유저가 수정·저장할 수 있다.
    (예: 목표-현재=2000, 불의 수정 100점 -> 20개)
    """

    def __init__(self, master, event, store):
        super().__init__(master, padding=14)
        self.event = event
        self.store = store
        self.key = event["_key"]
        saved = store.event(self.key)
        saved_points = saved.get("points", {})

        self.point_vars = []
        self.need_labels = []
        self._vcmd = (self.register(is_number), "%P")  # 숫자만 입력 허용

        # --- 타이틀 + 보상 아이콘 나열 ---
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

        ttk.Separator(self).pack(fill="x", pady=6)

        # --- 현재 / 목표 점수 ---
        score_row = ttk.Frame(self)
        score_row.pack(fill="x", pady=(0, 4))
        ttk.Label(score_row, text="현재 점수:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.current_var = tk.StringVar(value=saved.get("current", ""))
        self.current_var.trace_add("write", lambda *a, v=self.current_var: comma_format(v) or self.recalc())
        comma_format(self.current_var)
        _ce = ttk.Entry(score_row, textvariable=self.current_var, width=12, justify="right")
        _ce.pack(side="left", padx=(4, 16))
        _ce.bind("<FocusOut>", lambda e: self.recalc())
        ttk.Label(score_row, text="목표 점수:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.target_var = tk.StringVar(value=saved.get("target", ""))
        self.target_var.trace_add("write", lambda *a, v=self.target_var: comma_format(v) or self.recalc())
        comma_format(self.target_var)
        _te = ttk.Entry(score_row, textvariable=self.target_var, width=12, justify="right")
        _te.pack(side="left", padx=4)
        _te.bind("<FocusOut>", lambda e: self.recalc())

        # 필요 점수 표시
        self.gap_label = ttk.Label(self, text="", font=("Segoe UI", 11, "bold"), foreground="#1a5fb4")
        self.gap_label.pack(anchor="w", pady=(2, 6))

        ttk.Separator(self).pack(fill="x", pady=2)

        # --- 항목 리스트 (배점 수정 가능 + 필요 수량 자동 계산) ---
        rows = ttk.Frame(self)
        rows.pack(fill="x", pady=(4, 0))
        # 모든 메뉴에서 컬럼 간격을 동일하게: 항목 폭을 전체 최장 항목명에 맞춰 고정
        rows.columnconfigure(0, minsize=item_col_minsize())
        rows.columnconfigure(1, minsize=70)
        rows.columnconfigure(2, minsize=90)
        bold = ("Segoe UI", 10, "bold")
        ttk.Label(rows, text="항목", font=bold).grid(row=0, column=0, sticky="w", padx=3, pady=(0, 2))
        ttk.Label(rows, text="배점", font=bold).grid(row=0, column=1, sticky="e", padx=3, pady=(0, 2))
        ttk.Label(rows, text="필요 수량", font=bold).grid(row=0, column=2, sticky="e", padx=3, pady=(0, 2))

        for i, item in enumerate(event["items"], start=1):
            ttk.Label(rows, text=item["name"]).grid(row=i, column=0, sticky="w", padx=3, pady=2)

            pvar = tk.StringVar(value=saved_points.get(item["name"], str(item["points"])))
            pvar.trace_add("write", lambda *a: self.recalc())
            ttk.Entry(rows, textvariable=pvar, width=8, justify="right",
                      validate="key", validatecommand=self._vcmd).grid(row=i, column=1, sticky="e", padx=3, pady=2)
            self.point_vars.append(pvar)

            need = ttk.Label(rows, text="-", anchor="e", font=("Segoe UI", 10))
            need.grid(row=i, column=2, sticky="e", padx=3, pady=2)
            self.need_labels.append(need)

        self.recalc()

    def recalc(self):
        current = to_num(self.current_var.get())
        target = to_num(self.target_var.get())
        gap = target - current

        if target <= 0:
            self.gap_label.config(text="목표 점수를 입력하세요.")
        elif gap <= 0:
            self.gap_label.config(text=f"이미 목표 달성! ({int(-gap):,} 점 초과)")
        else:
            self.gap_label.config(text=f"필요 점수 (목표 - 현재): {int(gap):,} 점")

        for pvar, lbl in zip(self.point_vars, self.need_labels):
            pts = to_num(pvar.get())
            if target <= 0 or gap <= 0:
                lbl.config(text="0개" if gap <= 0 and target > 0 else "-")
            elif pts <= 0:
                lbl.config(text="—")
            else:
                lbl.config(text=f"{math.ceil(gap / pts):,}개")

        # 저장 (현재/목표/배점)
        rec = self.store.event(self.key)
        rec["current"] = self.current_var.get()
        rec["target"] = self.target_var.get()
        rec["points"] = {item["name"]: p.get()
                         for item, p in zip(self.event["items"], self.point_vars)}
        self.store.schedule_save()
