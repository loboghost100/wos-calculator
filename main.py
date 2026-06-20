"""WOS (White Out Survival) 이벤트 계산기

목표 점수까지 필요한 양을 계산한다.
- 왼쪽: 트리 사이드바 (그룹 -> 하위 이벤트, 펼침/접힘)
- 오른쪽: 선택한 이벤트의 계산기 (수량 입력 -> 점수 자동 합산)

새 이벤트 추가 = 아래 EVENT_GROUPS 데이터에 항목 추가하면 끝.
"""
import os
import sys
import json
import math
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


def _resource(*parts):
    """번들된 리소스 경로 (PyInstaller는 임시폴더 _MEIPASS에 풀어둠).
    예: _resource("assets", "icon.ico")
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


_ITEM_COL_MIN = None


def _item_col_minsize():
    """모든 이벤트의 항목명 중 가장 긴 폭(px). 4개 메뉴의 컬럼 정렬을 통일하기 위함."""
    global _ITEM_COL_MIN
    if _ITEM_COL_MIN is None:
        import tkinter.font as tkfont
        f = tkfont.Font(font=("Segoe UI", 10))
        widest = 0
        for group in EVENT_GROUPS:
            for ev in group["events"]:
                for it in ev["items"]:
                    widest = max(widest, f.measure(it["name"]))
        _ITEM_COL_MIN = widest + 12
    return _ITEM_COL_MIN


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
        return self.data.setdefault(
            key, {"current": "", "target": "", "items": {}, "points": {}}
        )

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
def _placeholder(name, icon=None):
    """아직 내용 미정인 자리표시용 이벤트."""
    return {
        "name": name,
        "icon": icon,
        "rewards": [],
        "items": [{"name": "(행동 미정)", "points": 0}],
    }


def _event(name, items, icon=None, rewards=None):
    """(이름, [(항목명, 기본배점), ...], 사이드바 아이콘, 보상 아이콘 목록) -> 이벤트 dict."""
    return {
        "name": name,
        "icon": icon,
        "rewards": rewards or [],
        "items": [{"name": n, "points": p} for n, p in items],
    }


EVENT_GROUPS = [
    {
        "name": "시간",
        "events": [],  # 이벤트가 아닌 별개 기능 -> 하위 항목 없이 단독 버튼
    },
    {
        "name": "개인 이벤트",
        "events": [
            _event("군비 경쟁1", [
                ("불의 수정", 100),
                ("불의 수정 조각", 50),
                ("제련된 불의 수정", 0),
                ("영주 장비", 3),
                ("레어 영웅 파편", 15),
                ("에픽 영웅 파편", 50),
                ("레전드 영웅 파편", 125),
                ("건설·연구·훈련 가속", 1),
                ("전문가 표식", 200),
                ("학문의 책", 2),
            ], icon="icon_arms.png", rewards=[
                "icon_diamond.png",
                "icon_legend_charm_part.png",
                "icon_design_plan.png",
                "icon_legend_skillbook.png",
            ]),
            _event("군비 경쟁2", [
                ("불의 수정", 100),
                ("불의 수정 조각", 50),
                ("제련된 불의 수정", 0),
                ("영주 장비", 3),
                ("마스터리석", 30),
                ("미스릴", 10),
                ("전용 장비", 5),
                ("건설·연구·훈련 가속", 1),
            ], icon="icon_arms.png", rewards=[
                "icon_diamond.png",
                "icon_legend_charm_part.png",
                "icon_legend_skillbook.png",
                "icon_legend_explore_skillbook.png",
            ]),
            _event("사관의 계획1", [
                ("영주 보석", 50),
                ("마스터리석", 30),
                ("전용 장비", 5),
                ("병사 훈련", 1),
            ], icon="icon_saquan.png", rewards=[
                "icon_diamond.png",
                "icon_legend_charm_part.png",
                "icon_mastery_stone.png",
                "icon_legend_skillbook.png",
            ]),
            _event("사관의 계획2", [
                ("영주 장비", 3),
                ("레어 영웅 파편", 15),
                ("에픽 영웅 파편", 50),
                ("레전드 영웅 파편", 125),
                ("마스터리석", 30),
                ("전용 장비", 5),
                ("미스릴", 10),
            ], icon="icon_saquan.png", rewards=[
                "icon_diamond.png",
                "icon_legend_charm_part.png",
                "icon_legend_skillbook.png",
                "icon_charm_design.png",
            ]),
        ],
    },
    {
        "name": "연맹 이벤트",
        "events": [
            _placeholder("최강 왕국"),
            _placeholder("연맹 대작전"),
            _placeholder("빙원의 왕"),
            _placeholder("연맹 총동원"),
        ],
    },
]

# 저장/복원용 안정적인 키 부여 ("그룹명::이벤트명")
for _group in EVENT_GROUPS:
    for _event in _group["events"]:
        _event["_key"] = f'{_group["name"]}::{_event["name"]}'


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

        # --- 타이틀 + 보상 아이콘 나열 ---
        header = ttk.Frame(self)
        header.pack(fill="x", anchor="w")
        ttk.Label(header, text=event["name"], font=("Segoe UI", 14, "bold")).pack(side="left")
        self._reward_imgs = []  # GC 방지용 참조 보관
        for j, icon in enumerate(event.get("rewards", [])):
            try:
                img = tk.PhotoImage(file=_resource("assets", icon))
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
        self.current_var.trace_add("write", lambda *a: self.recalc())
        ttk.Entry(score_row, textvariable=self.current_var, width=12, justify="right").pack(side="left", padx=(4, 16))
        ttk.Label(score_row, text="목표 점수:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.target_var = tk.StringVar(value=saved.get("target", ""))
        self.target_var.trace_add("write", lambda *a: self.recalc())
        ttk.Entry(score_row, textvariable=self.target_var, width=12, justify="right").pack(side="left", padx=4)

        # 필요 점수 표시
        self.gap_label = ttk.Label(self, text="", font=("Segoe UI", 11, "bold"), foreground="#1a5fb4")
        self.gap_label.pack(anchor="w", pady=(2, 6))

        ttk.Separator(self).pack(fill="x", pady=2)

        # --- 항목 리스트 (배점 수정 가능 + 필요 수량 자동 계산) ---
        rows = ttk.Frame(self)
        rows.pack(fill="x", pady=(4, 0))
        # 모든 메뉴에서 컬럼 간격을 동일하게: 항목 폭을 전체 최장 항목명에 맞춰 고정
        rows.columnconfigure(0, minsize=_item_col_minsize())
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
            ttk.Entry(rows, textvariable=pvar, width=8, justify="right").grid(row=i, column=1, sticky="e", padx=3, pady=2)
            self.point_vars.append(pvar)

            need = ttk.Label(rows, text="-", anchor="e", font=("Segoe UI", 10))
            need.grid(row=i, column=2, sticky="e", padx=3, pady=2)
            self.need_labels.append(need)

        self.recalc()

    @staticmethod
    def _to_num(s):
        try:
            return float(s.replace(",", "").strip() or 0)
        except ValueError:
            return 0

    def recalc(self):
        current = self._to_num(self.current_var.get())
        target = self._to_num(self.target_var.get())
        gap = target - current

        if target <= 0:
            self.gap_label.config(text="목표 점수를 입력하세요.")
        elif gap <= 0:
            self.gap_label.config(text=f"이미 목표 달성! ({int(-gap):,} 점 초과)")
        else:
            self.gap_label.config(text=f"필요 점수 (목표 - 현재): {int(gap):,} 점")

        for pvar, lbl in zip(self.point_vars, self.need_labels):
            pts = self._to_num(pvar.get())
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
        self.active = None           # 현재 선택된 항목(primary 위젯)
        self.first = None            # (primary, payload) 자동 선택용

        for group in EVENT_GROUPS:
            if group["events"]:
                self._add_group(group)
            else:
                self._add_standalone(group)

    def _add_standalone(self, group):
        # 하위 항목 없는 단독 항목 (이벤트가 아닌 별개 기능)
        payload = {"name": group["name"], "page": "standalone"}
        row = tk.Frame(self, bg=GROUP_BG, cursor="hand2")
        lbl = tk.Label(row, text=group["name"], bg=GROUP_BG, fg=FG,
                       font=("Segoe UI", 11, "bold"), anchor="w")
        lbl.pack(side="left", padx=12, pady=10)
        row.pack(fill="x")
        self._make_selectable(row, [row, lbl], GROUP_BG, GROUP_HOVER, payload)

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
        # Frame + (아이콘 라벨) + 텍스트 라벨 -> 아이콘/텍스트 간격을 직접 제어
        row = tk.Frame(parent, bg=SUB_BG, cursor="hand2")
        targets = [row]
        text_padx = (14, 14)
        icon = event.get("icon")
        if icon:
            try:
                img = tk.PhotoImage(file=_resource("assets", icon))
                il = tk.Label(row, image=img, bg=SUB_BG)
                il.image = img  # 가비지 컬렉션 방지
                il.pack(side="left", padx=(14, 0), pady=6)
                targets.append(il)
                text_padx = (0, 14)
            except Exception:
                pass
        tl = tk.Label(row, text=event["name"], bg=SUB_BG, fg=FG,
                      font=("Segoe UI", 10), anchor="w")
        tl.pack(side="left", padx=text_padx, pady=6)
        targets.append(tl)
        row.pack(fill="x")
        self._make_selectable(row, targets, SUB_BG, SUB_HOVER, event)

    def _make_selectable(self, primary, targets, normal, hover, payload):
        primary._paint = targets
        primary._normal_bg = normal
        for w in targets:
            w.bind("<Button-1>", lambda e, p=primary, pl=payload: self._select(p, pl))
            w.bind("<Enter>", lambda e, p=primary, h=hover: self._paint(p, h) if p is not self.active else None)
            w.bind("<Leave>", lambda e, p=primary, n=normal: self._paint(p, n) if p is not self.active else None)
        if self.first is None:
            self.first = (primary, payload)

    def _paint(self, primary, color):
        for w in primary._paint:
            w.config(bg=color)

    def _hover(self, btn, normal, hover):
        # 그룹 헤더(단일 버튼)용 호버
        btn.bind("<Enter>", lambda e: btn.config(bg=hover))
        btn.bind("<Leave>", lambda e: btn.config(bg=normal))

    def _select(self, primary, payload):
        if self.active is not None:
            self._paint(self.active, self.active._normal_bg)
        self.active = primary
        self._paint(primary, SUB_ACTIVE)
        self.on_event_select(payload)

    def select_first(self):
        if self.first:
            primary, payload = self.first
            self._select(primary, payload)


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
        self.geometry("780x640")
        try:
            self.iconbitmap(_resource("assets", "icon.ico"))
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
