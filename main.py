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
from datetime import datetime

APP_TITLE = "WOS 이벤트 계산기"
BASE_TIME = 9 * 60  # AM 9:00 = 540분 (시간 페이지 기본값, 코드 고정)


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


def _resource(name):
    """번들된 리소스 경로 (PyInstaller는 임시폴더 _MEIPASS에 풀어둠)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


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

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.schedule_save()

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


class TimePage(ttk.Frame):
    """현재 PC 시간을 기준으로 등록된 시각과의 차이를 보여준다.

    - 기본값 AM 9:00은 코드 고정(삭제 불가)
    - 사용자가 시각 추가/삭제 가능 (userdata에 저장)
    - 12h / 24h 표시 전환 (내부 표현은 0~1439분으로 형식 무관)
    """

    def __init__(self, master, store):
        super().__init__(master, padding=14)
        self.store = store
        self.fmt = store.get("_time_format", "24h")
        self.user_times = sorted(set(store.get("_user_times", [])))
        self.rows = []          # [(target_min, diff_label)]
        self._after_id = None

        ttk.Label(self, text="시간", font=("Segoe UI", 14, "bold")).pack(anchor="w")

        # 현재 시간 + 형식 토글
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(6, 4))
        self.now_label = ttk.Label(top, text="", font=("Segoe UI", 11))
        self.now_label.pack(side="left")

        fmt_box = ttk.Frame(top)
        fmt_box.pack(side="right")
        ttk.Label(fmt_box, text="표시: ").pack(side="left")
        self.fmt_var = tk.StringVar(value=self.fmt)
        ttk.Radiobutton(fmt_box, text="24h", value="24h", variable=self.fmt_var,
                        command=self._on_format).pack(side="left")
        ttk.Radiobutton(fmt_box, text="12h", value="12h", variable=self.fmt_var,
                        command=self._on_format).pack(side="left")

        ttk.Separator(self).pack(fill="x", pady=6)

        # 시각 목록
        self.list_frame = ttk.Frame(self)
        self.list_frame.pack(fill="x")

        ttk.Separator(self).pack(fill="x", pady=8)

        # 시각 추가 컨트롤
        add = ttk.Frame(self)
        add.pack(fill="x")
        ttk.Label(add, text="시각 추가:").pack(side="left")
        self.add_hour = ttk.Spinbox(add, width=4, justify="right")
        self.add_hour.set("9")
        self.add_hour.pack(side="left", padx=(6, 0))
        ttk.Label(add, text=":").pack(side="left", padx=2)
        self.add_min = ttk.Spinbox(add, width=4, from_=0, to=59, justify="right")
        self.add_min.set("00")
        self.add_min.pack(side="left")
        self.add_period = ttk.Combobox(add, width=4, values=["AM", "PM"], state="readonly")
        self.add_period.current(0)
        self.add_period.pack(side="left", padx=6)
        ttk.Button(add, text="추가", command=self._add).pack(side="left", padx=4)

        self.msg = ttk.Label(self, text="", foreground="#c01c28")
        self.msg.pack(anchor="w", pady=(4, 0))

        self._sync_add_controls()
        self._render_list()
        self._tick()

    # --- 시각 표현 ---
    def _fmt_time(self, minutes):
        h, m = divmod(minutes % (24 * 60), 60)
        if self.fmt == "12h":
            period = "AM" if h < 12 else "PM"
            h12 = h % 12 or 12
            return f"{period} {h12}:{m:02d}"
        return f"{h:02d}:{m:02d}"

    def _diff_text(self, target, now_min):
        # 목표 시각은 항상 미래 -> 다음 발생까지 남은 시간 (오늘 지났으면 내일)
        diff = (target - now_min) % (24 * 60)
        if diff == 0:
            return "지금"
        h, m = divmod(diff, 60)
        return f"{h}시간 {m}분 남음"

    # --- 추가/삭제 ---
    def _parse_add(self):
        try:
            h = int(self.add_hour.get())
            m = int(self.add_min.get() or 0)
        except (ValueError, TypeError):
            return None
        if not (0 <= m <= 59):
            return None
        if self.fmt == "12h":
            if not (1 <= h <= 12):
                return None
            if self.add_period.get() == "AM":
                h = 0 if h == 12 else h
            else:
                h = 12 if h == 12 else h + 12
        elif not (0 <= h <= 23):
            return None
        return h * 60 + m

    def _add(self):
        mins = self._parse_add()
        if mins is None:
            self.msg.config(text="시각 형식이 올바르지 않습니다.")
            return
        if mins == BASE_TIME or mins in self.user_times:
            self.msg.config(text="이미 등록된 시각입니다.")
            return
        self.user_times = sorted(set(self.user_times) | {mins})
        self.store.set("_user_times", self.user_times)
        self.msg.config(text="")
        self._render_list()

    def _delete(self, mins):
        if mins in self.user_times:
            self.user_times.remove(mins)
            self.store.set("_user_times", self.user_times)
            self._render_list()

    # --- 형식 토글 ---
    def _on_format(self):
        self.fmt = self.fmt_var.get()
        self.store.set("_time_format", self.fmt)
        self._sync_add_controls()
        self._render_list()

    def _sync_add_controls(self):
        if self.fmt == "12h":
            self.add_hour.config(from_=1, to=12)
            self.add_period.configure(state="readonly")
        else:
            self.add_hour.config(from_=0, to=23)
            self.add_period.configure(state="disabled")

    # --- 목록 렌더링 + 라이브 갱신 ---
    def _render_list(self):
        for c in self.list_frame.winfo_children():
            c.destroy()
        self.rows = []
        # 기본값 포함 전체를 시각 순으로 정렬
        all_times = sorted(set(self.user_times) | {BASE_TIME})
        entries = [(t, t == BASE_TIME) for t in all_times]
        for target, is_base in entries:
            row = ttk.Frame(self.list_frame)
            row.pack(fill="x", pady=2)
            name = self._fmt_time(target) + ("  (기본)" if is_base else "")
            ttk.Label(row, text=name, width=16, font=("Segoe UI", 11)).pack(side="left")
            diff_lbl = ttk.Label(row, text="", font=("Segoe UI", 11), foreground="#1a5fb4")
            diff_lbl.pack(side="left", padx=8)
            self.rows.append((target, diff_lbl))
            if not is_base:
                ttk.Button(row, text="삭제", width=5,
                           command=lambda t=target: self._delete(t)).pack(side="right")
        self._refresh_diffs()

    def _refresh_diffs(self):
        now = datetime.now()
        now_min = now.hour * 60 + now.minute
        for target, lbl in self.rows:
            lbl.config(text=self._diff_text(target, now_min))

    def _tick(self):
        now = datetime.now()
        if self.fmt == "12h":
            period = "AM" if now.hour < 12 else "PM"
            h12 = now.hour % 12 or 12
            now_str = f"{period} {h12}:{now.minute:02d}"
        else:
            now_str = f"{now.hour:02d}:{now.minute:02d}"
        self.now_label.config(text="현재 시간: " + now_str)
        self._refresh_diffs()
        self._after_id = self.after(1000, self._tick)

    def destroy(self):
        if self._after_id:
            self.after_cancel(self._after_id)
        super().destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("740x540")
        try:
            self.iconbitmap(_resource("icon.ico"))
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
                if payload["name"] == "시간":
                    self.calcs[key] = TimePage(self.right, self.store)
                else:
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
