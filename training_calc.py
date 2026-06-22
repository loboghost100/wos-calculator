"""연맹 총동원 — 훈련 계획 계산기.

세 병영(방패/창병/궁병)을 같은 시간 동안 동시에 훈련해서, 합산 전투력이
목표가 되도록 필요 시간과 병종별 마릿수·전투력을 계산한다.

공식:
  효율ᵢ = 전투력ᵢ / 시간ᵢ          (초당 전투력)
  필요시간 T = 목표 / Σ효율ᵢ
  마릿수ᵢ = T / 시간ᵢ,  전투력ᵢ = 마릿수ᵢ × 전투력ᵢ
"""
import tkinter as tk
from tkinter import ttk

from resources import is_number, comma_format, comma_normalize, to_num

# (표시명, 저장키, 기본 전투력, 기본 훈련시간초)
TROOPS = [
    ("방패병", "shield", 135, 49),
    ("창병", "spear", 110, 42),
    ("궁병", "archer", 110, 42),
]


def _fmt_time(sec):
    sec = int(round(sec))
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    parts = []
    if h:
        parts.append(f"{h}시간")
    if m:
        parts.append(f"{m}분")
    parts.append(f"{s}초")
    return " ".join(parts)


class TrainingCalc(ttk.Frame):
    def __init__(self, master, event, store):
        super().__init__(master, padding=14)
        self.event = event
        self.store = store
        self.key = event["_key"]
        saved = store.event(self.key)
        self._vcmd = (self.register(is_number), "%P")
        self.troop_vars = []  # recalc가 먼저 불려도 안전하게 빈 리스트로 초기화

        ttk.Label(self, text=event["name"], font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Separator(self).pack(fill="x", pady=6)

        # --- 목표 전투력 ---
        trow = ttk.Frame(self)
        trow.pack(fill="x", pady=(0, 6))
        ttk.Label(trow, text="목표 전투력:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.target_var = tk.StringVar(value=saved.get("target") or "120000")
        self.target_var.trace_add("write", lambda *a, v=self.target_var: (comma_format(v), self.recalc()))
        comma_format(self.target_var)
        _e = ttk.Entry(trow, textvariable=self.target_var, width=14, justify="right")
        _e.pack(side="left", padx=6)
        _e.bind("<FocusOut>", lambda e, v=self.target_var: (comma_normalize(v), self.recalc()))

        ttk.Separator(self).pack(fill="x", pady=2)

        # --- 병종별 전투력 / 훈련시간 입력 ---
        grid = ttk.Frame(self)
        grid.pack(fill="x", pady=(4, 0))
        bold = ("Segoe UI", 10, "bold")
        ttk.Label(grid, text="병종", font=bold).grid(row=0, column=0, sticky="w", padx=3, pady=(0, 2))
        ttk.Label(grid, text="전투력", font=bold).grid(row=0, column=1, padx=3, pady=(0, 2))
        ttk.Label(grid, text="훈련시간(초)", font=bold).grid(row=0, column=2, padx=3, pady=(0, 2))

        self.troop_vars = []  # [(name, power_var, time_var)]
        for i, (name, key, dp, dt) in enumerate(TROOPS, start=1):
            ttk.Label(grid, text=name).grid(row=i, column=0, sticky="w", padx=3, pady=2)
            pvar = tk.StringVar(value=saved.get("p_" + key) or str(dp))
            tvar = tk.StringVar(value=saved.get("t_" + key) or str(dt))
            pvar.trace_add("write", lambda *a: self.recalc())
            tvar.trace_add("write", lambda *a: self.recalc())
            ttk.Entry(grid, textvariable=pvar, width=8, justify="right",
                      validate="key", validatecommand=self._vcmd).grid(row=i, column=1, padx=3, pady=2)
            ttk.Entry(grid, textvariable=tvar, width=10, justify="right",
                      validate="key", validatecommand=self._vcmd).grid(row=i, column=2, padx=3, pady=2)
            self.troop_vars.append((name, key, pvar, tvar))

        ttk.Separator(self).pack(fill="x", pady=8)

        # --- 결과 ---
        self.result = ttk.Label(self, text="", font=("Segoe UI", 11), justify="left", foreground="#1a5fb4")
        self.result.pack(anchor="w")

        self.recalc()

    def recalc(self):
        target = to_num(self.target_var.get())
        rows = []          # (name, power, time, eff)
        total_eff = 0.0
        for name, key, pvar, tvar in self.troop_vars:
            p = to_num(pvar.get())
            t = to_num(tvar.get())
            eff = p / t if t > 0 else 0.0
            total_eff += eff
            rows.append((name, p, t, eff))

        if target > 0 and total_eff > 0:
            big_t = target / total_eff
            lines = [f"필요 시간: {_fmt_time(big_t)}", ""]
            total_power = 0.0
            for name, p, t, eff in rows:
                units = int(round(big_t / t)) if t > 0 else 0
                actual_t = units * t          # 정수 마릿수 기준 실제 훈련 시간
                power = units * p
                total_power += power
                lines.append(f"  {name}: {units:,}명 · {_fmt_time(actual_t)}  →  {int(round(power)):,} 전투력")
            lines.append("")
            lines.append(f"합계: 약 {int(round(total_power)):,} 전투력")
            self.result.config(text="\n".join(lines))
        else:
            self.result.config(text="목표 전투력과 병종별 전투력·훈련시간을 입력하세요.")

        self._save()

    def _save(self):
        rec = self.store.event(self.key)
        rec["target"] = self.target_var.get()
        for name, key, pvar, tvar in self.troop_vars:
            rec["p_" + key] = pvar.get()
            rec["t_" + key] = tvar.get()
        self.store.schedule_save()
