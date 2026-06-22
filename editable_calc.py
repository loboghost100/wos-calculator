"""보기/편집 토글이 있는 계산기.

- 보기 모드(기본): 항목·배점 읽기전용, 현재/목표 점수로 필요 수량 계산
- 편집 모드([편집]→[완료]): 항목 이름·배점 수정, 추가/삭제
항목과 점수는 userdata에 저장된다 (키는 event["_key"]).
"""
import tkinter as tk
from tkinter import ttk

from resources import (resource, is_number, comma_format, comma_normalize, to_num,
                       gap_text, need_text)
from config import item_col_minsize


def _fmt_points(v):
    """배점 표시: 정수면 정수로, 소수가 있으면 1자리까지 (천단위 콤마)."""
    if abs(v - round(v)) < 1e-9:
        return f"{int(round(v)):,}"
    return f"{v:,.1f}"


class EditableCalc(ttk.Frame):
    def __init__(self, master, event, store, show_header=True):
        super().__init__(master, padding=14 if show_header else 0)
        self.event = event
        self.store = store
        self.key = event["_key"]
        saved = store.event(self.key)
        # 저장된 편집 내역이 있으면 그걸, 없으면 config 기본 항목을 초기값으로
        saved_items = saved.get("custom_items")
        if saved_items is not None:
            self.items = [dict(it) for it in saved_items]
        else:
            self.items = [{"name": it["name"], "points": str(it["points"])}
                          for it in event.get("items", [])]
        self.editing = False
        self._vcmd = (self.register(is_number), "%P")
        self.need_labels = []
        self.name_vars = []
        self.point_vars = []
        self._reward_imgs = []  # GC 방지용 참조 보관

        if show_header:
            header = ttk.Frame(self)
            header.pack(fill="x", anchor="w")
            ttk.Label(header, text=event["name"], font=("Segoe UI", 14, "bold")).pack(side="left")
            if event.get("custom"):
                # Custom 탭: 이름 옆에 유저 제목 입력칸
                self.title_var = tk.StringVar(value=saved.get("title", ""))
                self.title_var.trace_add("write", lambda *a: self._save_title())
                ttk.Entry(header, textvariable=self.title_var, width=24,
                          font=("Segoe UI", 12)).pack(side="left", padx=(10, 0))
            for j, icon in enumerate(event.get("rewards", [])):
                try:
                    img = tk.PhotoImage(file=resource("assets", icon))
                except Exception:
                    continue
                self._reward_imgs.append(img)
                ttk.Label(header, image=img).pack(side="left", padx=(12 if j == 0 else 4, 0))
            ttk.Separator(self).pack(fill="x", pady=6)

        # --- 목표 / 현재 점수 ---
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

        # --- 항목 표 ---
        self.list_frame = ttk.Frame(self)
        self.list_frame.pack(fill="x", pady=(4, 0))
        self._render()

    def _toggle_edit(self):
        self.editing = not self.editing
        self._render()

    def _render(self):
        for c in self.list_frame.winfo_children():
            c.destroy()
        self.list_frame.columnconfigure(0, minsize=item_col_minsize())
        self.list_frame.columnconfigure(1, minsize=70)
        self.list_frame.columnconfigure(2, minsize=90)
        self.list_frame.columnconfigure(3, weight=1)  # 남는 공간 흡수 -> 편집 버튼 우측 정렬
        bold = ("Segoe UI", 10, "bold")
        ttk.Label(self.list_frame, text="항목", font=bold).grid(row=0, column=0, sticky="w", padx=3, pady=(0, 2))
        ttk.Label(self.list_frame, text="배점", font=bold).grid(row=0, column=1, sticky="e", padx=3, pady=(0, 2))
        if not self.editing:
            ttk.Label(self.list_frame, text="필요 수량", font=bold).grid(row=0, column=2, sticky="e", padx=3, pady=(0, 2))
        # 편집 토글 버튼: 헤더와 같은 줄 오른쪽
        ttk.Button(self.list_frame, text=("완료" if self.editing else "편집"), width=6,
                   command=self._toggle_edit).grid(row=0, column=3, sticky="e", padx=(8, 3), pady=(0, 2))

        self.need_labels = []
        self.name_vars = []
        self.point_vars = []

        if not self.items:
            msg = "(아래에서 항목을 추가하세요)" if self.editing else "(항목 없음 — '편집'으로 추가)"
            ttk.Label(self.list_frame, text=msg, foreground="gray").grid(
                row=1, column=0, columnspan=4, sticky="w", padx=3, pady=6)

        for i, it in enumerate(self.items, start=1):
            if self.editing:
                nvar = tk.StringVar(value=it["name"])
                nvar.trace_add("write", lambda *a, idx=i - 1, v=nvar: self._on_name(idx, v))
                ttk.Entry(self.list_frame, textvariable=nvar, width=18).grid(
                    row=i, column=0, sticky="w", padx=3, pady=2)
                self.name_vars.append(nvar)

                pvar = tk.StringVar(value=str(it.get("points", "0")))
                pvar.trace_add("write", lambda *a, idx=i - 1, v=pvar: self._on_points(idx, v))
                ttk.Entry(self.list_frame, textvariable=pvar, width=8, justify="right",
                          validate="key", validatecommand=self._vcmd).grid(
                    row=i, column=1, sticky="e", padx=3, pady=2)
                self.point_vars.append(pvar)

                ttk.Button(self.list_frame, text="삭제", width=5,
                           command=lambda idx=i - 1: self._delete(idx)).grid(
                    row=i, column=2, padx=(8, 3), pady=2)
            else:
                ttk.Label(self.list_frame, text=it["name"]).grid(row=i, column=0, sticky="w", padx=3, pady=2)
                ttk.Label(self.list_frame, text=_fmt_points(to_num(it.get("points", "0"))),
                          anchor="e", font=("Segoe UI", 10)).grid(row=i, column=1, sticky="e", padx=3, pady=2)
                need = ttk.Label(self.list_frame, text="-", anchor="e", font=("Segoe UI", 10))
                need.grid(row=i, column=2, sticky="e", padx=3, pady=2)
                self.need_labels.append(need)

        if self.editing:
            r = len(self.items) + 1
            addf = ttk.Frame(self.list_frame)
            addf.grid(row=r, column=0, columnspan=4, sticky="w", pady=(8, 0))
            ttk.Label(addf, text="항목 추가:").pack(side="left")
            self.add_name = ttk.Entry(addf, width=16)
            self.add_name.pack(side="left", padx=(6, 4))
            ttk.Label(addf, text="배점").pack(side="left")
            self.add_points = ttk.Entry(addf, width=8, justify="right",
                                        validate="key", validatecommand=self._vcmd)
            self.add_points.pack(side="left", padx=4)
            self.add_points.bind("<Return>", lambda e: self._add())
            ttk.Button(addf, text="추가", command=self._add).pack(side="left", padx=6)

        self.recalc()

    def _add(self):
        name = self.add_name.get().strip()
        if not name:
            return
        self.items.append({"name": name, "points": self.add_points.get().strip() or "0"})
        self._save_items()
        self._render()
        self.add_name.focus_set()  # 연속 입력: 추가 후 이름칸으로 포커스 복귀

    def _delete(self, idx):
        if 0 <= idx < len(self.items):
            del self.items[idx]
            self._save_items()
            self._render()

    def _on_name(self, idx, var):
        if 0 <= idx < len(self.items):
            self.items[idx]["name"] = var.get()
            self._save_items()

    def _on_points(self, idx, var):
        if 0 <= idx < len(self.items):
            self.items[idx]["points"] = var.get()
            self._save_items()

    def recalc(self):
        current = to_num(self.current_var.get())
        target = to_num(self.target_var.get())
        gap = target - current
        self.gap_label.config(text=gap_text(target, current))
        if not self.editing:
            for it, lbl in zip(self.items, self.need_labels):
                lbl.config(text=need_text(gap, target, to_num(it.get("points", "0"))))
        self._save_scores()

    def _save_scores(self):
        # 현재/목표 점수만 저장 (항목은 편집 전까지 건드리지 않아 기본값 유지)
        rec = self.store.event(self.key)
        rec["current"] = self.current_var.get()
        rec["target"] = self.target_var.get()
        self.store.schedule_save()

    def _save_items(self):
        # 유저가 항목을 편집했을 때만 custom_items 저장 (기본값 위에 덮어씀)
        rec = self.store.event(self.key)
        rec["custom_items"] = self.items
        self.store.schedule_save()

    def _save_title(self):
        rec = self.store.event(self.key)
        rec["title"] = self.title_var.get()
        self.store.schedule_save()
