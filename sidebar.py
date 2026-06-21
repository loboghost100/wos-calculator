"""버튼 느낌의 아코디언 사이드바."""
import tkinter as tk

from resources import resource
from config import EVENT_GROUPS

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
        targets = [row]
        text_padx = 12
        icon = group.get("icon")
        if icon:
            try:
                img = tk.PhotoImage(file=resource("assets", icon))
                il = tk.Label(row, image=img, bg=GROUP_BG)
                il.image = img  # GC 방지
                il.pack(side="left", padx=(12, 0), pady=10)
                targets.append(il)
                text_padx = (0, 12)
            except Exception:
                pass
        lbl = tk.Label(row, text=group["name"], bg=GROUP_BG, fg=FG,
                       font=("Segoe UI", 11, "bold"), anchor="w")
        lbl.pack(side="left", padx=text_padx, pady=10)
        targets.append(lbl)
        row.pack(fill="x")
        self._make_selectable(row, targets, GROUP_BG, GROUP_HOVER, payload)

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
                img = tk.PhotoImage(file=resource("assets", icon))
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
