"""유저가 항목/배점을 직접 추가·삭제하는 커스텀 이벤트 계산기."""
import math
import tkinter as tk
from tkinter import ttk, messagebox

from resources import is_number, comma_format, comma_normalize, to_num


class CustomEventCalc(ttk.Frame):
    """유저가 항목/배점을 직접 추가·삭제하는 커스텀 이벤트 계산기.

    현재/목표 점수는 일반 이벤트와 동일. 항목 목록은 userdata에 저장된다.
    """

    def __init__(self, master, event, store):
        super().__init__(master, padding=14)
        self.event = event
        self.store = store
        self.key = event["_key"]
        saved = store.event(self.key)
        self.items = [dict(it) for it in saved.get("custom_items", [])]  # [{name, points}]
        self.need_labels = []
        self._vcmd = (self.register(is_number), "%P")  # 숫자만 입력 허용

        # --- 타이틀 + 유저 제목 입력 ---
        header = ttk.Frame(self)
        header.pack(fill="x", anchor="w")
        ttk.Label(header, text=event["name"], font=("Segoe UI", 14, "bold")).pack(side="left")
        self.title_var = tk.StringVar(value=saved.get("title", ""))
        self.title_var.trace_add("write", lambda *a: self._save())
        ttk.Entry(header, textvariable=self.title_var, width=24, font=("Segoe UI", 12)).pack(side="left", padx=(10, 0))

        ttk.Separator(self).pack(fill="x", pady=6)

        # --- 목표 / 현재 점수 (현재 점수 옆 '적용' 버튼으로도 계산. 타이핑 자동 계산은 유지) ---
        score_row = ttk.Frame(self)
        score_row.pack(fill="x", pady=(0, 4))
        ttk.Label(score_row, text="목표 점수:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.target_var = tk.StringVar(value=saved.get("target", ""))
        self.target_var.trace_add("write", lambda *a, v=self.target_var: (comma_format(v), self.recalc()))
        comma_format(self.target_var)
        _te = ttk.Entry(score_row, textvariable=self.target_var, width=12, justify="right")
        _te.pack(side="left", padx=(4, 16))
        _te.bind("<FocusOut>", lambda e, v=self.target_var: (comma_normalize(v), self.recalc()))
        ttk.Label(score_row, text="현재 점수:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.current_var = tk.StringVar(value=saved.get("current", ""))
        self.current_var.trace_add("write", lambda *a, v=self.current_var: (comma_format(v), self.recalc()))
        comma_format(self.current_var)
        _ce = ttk.Entry(score_row, textvariable=self.current_var, width=12, justify="right")
        _ce.pack(side="left", padx=4)
        _ce.bind("<FocusOut>", lambda e, v=self.current_var: (comma_normalize(v), self.recalc()))

        self.gap_label = ttk.Label(self, text="", font=("Segoe UI", 11, "bold"), foreground="#1a5fb4")
        self.gap_label.pack(anchor="w", pady=(2, 6))

        ttk.Separator(self).pack(fill="x", pady=2)

        # --- 항목 추가 (목록 위에 고정) ---
        add = ttk.Frame(self)
        add.pack(fill="x", pady=(2, 0))
        ttk.Label(add, text="항목 추가:").pack(side="left")
        self.add_name = ttk.Entry(add, width=16)
        self.add_name.pack(side="left", padx=(6, 4))
        ttk.Label(add, text="배점").pack(side="left")
        self.add_points = ttk.Entry(add, width=8, justify="right",
                                    validate="key", validatecommand=self._vcmd)
        self.add_points.pack(side="left", padx=4)
        self.add_points.bind("<Return>", lambda e: self._add())  # 배점에서 엔터 = 추가
        ttk.Button(add, text="추가", command=self._add).pack(side="left", padx=6)
        ttk.Button(add, text="초기화", command=self._reset_items).pack(side="left")
        self.msg = ttk.Label(add, text="", foreground="#c01c28")
        self.msg.pack(side="left", padx=(8, 0))

        ttk.Separator(self).pack(fill="x", pady=(4, 2))

        # --- 항목 목록 (동적, 추가 필드 아래) ---
        self.list_frame = ttk.Frame(self)
        self.list_frame.pack(fill="x", pady=0)

        self._render()

    def _render(self):
        for c in self.list_frame.winfo_children():
            c.destroy()
        self.list_frame.columnconfigure(0, minsize=160)
        self.list_frame.columnconfigure(1, minsize=70)
        self.list_frame.columnconfigure(2, minsize=90)
        bold = ("Segoe UI", 10, "bold")
        ttk.Label(self.list_frame, text="항목", font=bold).grid(row=0, column=0, sticky="w", padx=3, pady=(0, 2))
        ttk.Label(self.list_frame, text="배점", font=bold).grid(row=0, column=1, sticky="e", padx=3, pady=(0, 2))
        ttk.Label(self.list_frame, text="필요 수량", font=bold).grid(row=0, column=2, sticky="e", padx=3, pady=(0, 2))

        self.need_labels = []
        if not self.items:
            ttk.Label(self.list_frame, text="(추가된 항목이 없습니다)", foreground="gray").grid(
                row=1, column=0, columnspan=4, sticky="w", padx=3, pady=6)

        for i, it in enumerate(self.items, start=1):
            ttk.Label(self.list_frame, text=it["name"]).grid(row=i, column=0, sticky="w", padx=3, pady=2)

            pvar = tk.StringVar(value=str(it.get("points", "0")))
            pvar.trace_add("write", lambda *a, idx=i - 1, var=pvar: self._on_points(idx, var))
            ttk.Entry(self.list_frame, textvariable=pvar, width=8, justify="right",
                      validate="key", validatecommand=self._vcmd).grid(
                row=i, column=1, sticky="e", padx=3, pady=2)

            need = ttk.Label(self.list_frame, text="-", anchor="e", font=("Segoe UI", 10))
            need.grid(row=i, column=2, sticky="e", padx=3, pady=2)
            self.need_labels.append(need)

            ttk.Button(self.list_frame, text="삭제", width=5,
                       command=lambda idx=i - 1: self._delete(idx)).grid(row=i, column=3, padx=(8, 3), pady=2)

        self.recalc()

    def _on_points(self, idx, var):
        if 0 <= idx < len(self.items):
            self.items[idx]["points"] = var.get()
            self.recalc()

    def _add(self):
        name = self.add_name.get().strip()
        if not name:
            self.msg.config(text="항목 이름을 입력하세요.")
            return
        points = self.add_points.get().strip() or "0"
        self.items.append({"name": name, "points": points})
        self.add_name.delete(0, "end")
        self.add_points.delete(0, "end")
        self.msg.config(text="")
        self._save()
        self._render()

    def _delete(self, idx):
        if 0 <= idx < len(self.items):
            del self.items[idx]
            self._save()
            self._render()

    def _reset_items(self):
        if not self.items:
            return
        if messagebox.askyesno("초기화", "추가한 항목을 모두 삭제할까요?"):
            self.items = []
            self._save()
            self._render()

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

        for it, lbl in zip(self.items, self.need_labels):
            pts = to_num(it.get("points", "0"))
            if target <= 0 or gap <= 0:
                lbl.config(text="0개" if gap <= 0 and target > 0 else "-")
            elif pts <= 0:
                lbl.config(text="—")
            else:
                lbl.config(text=f"{math.ceil(gap / pts):,}개")

        self._save()

    def _save(self):
        rec = self.store.event(self.key)
        rec["title"] = self.title_var.get()
        rec["current"] = self.current_var.get()
        rec["target"] = self.target_var.get()
        rec["custom_items"] = self.items
        self.store.schedule_save()
