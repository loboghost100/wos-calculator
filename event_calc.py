"""일반 이벤트 점수 계산기 (군비/사관 등)."""
import tkinter as tk
from tkinter import ttk

from resources import (resource, is_number, comma_format, comma_normalize,
                       to_num, gap_text, need_text)
from config import item_col_minsize


def _fmt_points(v):
    """배점 표시: 정수면 정수로, 소수가 있으면 1자리까지 (천단위 콤마)."""
    if abs(v - round(v)) < 1e-9:
        return f"{int(round(v)):,}"
    return f"{v:,.1f}"


class EventCalc(ttk.Frame):
    """이벤트 점수 계산기.

    현재 점수 / 목표 점수를 입력하면, 부족한 점수를 채우기 위해 각 항목을
    몇 개 써야 하는지 계산해서 보여준다. 배점은 유저가 수정·저장할 수 있다.
    (예: 목표-현재=2000, 불의 수정 100점 -> 20개)
    """

    def __init__(self, master, event, store, show_header=True,
                 bonus_getter=None, points_editable=True):
        super().__init__(master, padding=14 if show_header else 0)
        self.event = event
        self.store = store
        self.key = event["_key"]
        saved = store.event(self.key)
        saved_points = saved.get("points", {})
        defaults = event.get("defaults", {})

        # bonus_getter: 호출하면 배점 배율(1.5 등)을 돌려주는 함수 (None이면 보너스 없음)
        # points_editable: 배점을 유저가 직접 수정(True) / 기본 배점 고정·실효 배점 표시(False)
        self.bonus_getter = bonus_getter
        self.points_editable = points_editable

        self.item_names = [it["name"] for it in event["items"]]
        self.base_points = []     # 항목별 기본 배점(보너스 미반영)
        self.point_vars = []      # 편집 가능 모드: StringVar, 아니면 None
        self.point_labels = []    # 읽기전용 모드: 실효 배점 Label, 아니면 None
        self.need_labels = []
        self._vcmd = (self.register(is_number), "%P")  # 숫자만 입력 허용

        # --- 타이틀 + 보상 아이콘 나열 ---
        # (멀티데이 페이지에 본문으로 포함될 땐 타이틀/보상을 상위에서 한 번만 그리므로 생략)
        self._reward_imgs = []  # GC 방지용 참조 보관
        if show_header:
            header = ttk.Frame(self)
            header.pack(fill="x", anchor="w")
            ttk.Label(header, text=event["name"], font=("Segoe UI", 14, "bold")).pack(side="left")
            for j, icon in enumerate(event.get("rewards", [])):
                try:
                    img = tk.PhotoImage(file=resource("assets", icon))
                except Exception:
                    continue
                self._reward_imgs.append(img)
                ttk.Label(header, image=img).pack(side="left", padx=(12 if j == 0 else 4, 0))

            ttk.Separator(self).pack(fill="x", pady=6)

        # --- 목표 / 현재 점수 (현재 점수 옆 '적용' 버튼으로도 계산. 타이핑 자동 계산은 유지) ---
        score_row = ttk.Frame(self)
        score_row.pack(fill="x", pady=(0, 4))
        ttk.Label(score_row, text="목표 점수:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.target_var = tk.StringVar(value=saved.get("target") or defaults.get("target", ""))
        self.target_var.trace_add("write", lambda *a, v=self.target_var: (comma_format(v), self.recalc()))
        comma_format(self.target_var)
        _te = ttk.Entry(score_row, textvariable=self.target_var, width=12, justify="right")
        _te.pack(side="left", padx=(4, 16))
        _te.bind("<FocusOut>", lambda e, v=self.target_var: (comma_normalize(v), self.recalc()))
        ttk.Label(score_row, text="현재 점수:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.current_var = tk.StringVar(value=saved.get("current") or defaults.get("current", ""))
        self.current_var.trace_add("write", lambda *a, v=self.current_var: (comma_format(v), self.recalc()))
        comma_format(self.current_var)
        _ce = ttk.Entry(score_row, textvariable=self.current_var, width=12, justify="right")
        _ce.pack(side="left", padx=4)
        _ce.bind("<FocusOut>", lambda e, v=self.current_var: (comma_normalize(v), self.recalc()))

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
            self.base_points.append(float(item["points"]))

            if points_editable:
                pvar = tk.StringVar(value=saved_points.get(item["name"], str(item["points"])))
                pvar.trace_add("write", lambda *a: self.recalc())
                ttk.Entry(rows, textvariable=pvar, width=8, justify="right",
                          validate="key", validatecommand=self._vcmd).grid(row=i, column=1, sticky="e", padx=3, pady=2)
                self.point_vars.append(pvar)
                self.point_labels.append(None)
            else:
                # 배점 고정: 실효 배점(기본×배율)을 라벨로만 표시
                plabel = ttk.Label(rows, text="-", anchor="e", font=("Segoe UI", 10))
                plabel.grid(row=i, column=1, sticky="e", padx=3, pady=2)
                self.point_vars.append(None)
                self.point_labels.append(plabel)

            need = ttk.Label(rows, text="-", anchor="e", font=("Segoe UI", 10))
            need.grid(row=i, column=2, sticky="e", padx=3, pady=2)
            self.need_labels.append(need)

        self.recalc()

    def recalc(self):
        current = to_num(self.current_var.get())
        target = to_num(self.target_var.get())
        gap = target - current
        self.gap_label.config(text=gap_text(target, current))

        mult = self.bonus_getter() if self.bonus_getter else 1.0
        for i, (need_lbl, plabel) in enumerate(zip(self.need_labels, self.point_labels)):
            # 기본 배점: 편집 모드면 입력값, 고정 모드면 config 값
            base = to_num(self.point_vars[i].get()) if self.point_vars[i] is not None \
                else self.base_points[i]
            eff = base * mult                      # 실효 배점 = 기본 × 배율
            if plabel is not None:
                plabel.config(text=_fmt_points(eff))
            need_lbl.config(text=need_text(gap, target, eff))

        # 저장 (현재/목표 + 편집 가능한 경우에만 기본 배점)
        rec = self.store.event(self.key)
        rec["current"] = self.current_var.get()
        rec["target"] = self.target_var.get()
        if self.points_editable:
            rec["points"] = {name: p.get()
                             for name, p in zip(self.item_names, self.point_vars)}
        self.store.schedule_save()
