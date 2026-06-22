"""앱 상수 + 이벤트 데이터 정의.

이벤트 데이터 (그룹 -> 이벤트):
  group.name   : 사이드바 상위 항목(펼쳐지는 그룹)
  event.name   : 하위 항목(클릭 시 오른쪽에 계산기 표시)
  event.icon   : 사이드바 아이콘 파일명 (assets/ 기준)
  event.rewards: 타이틀 옆 보상 아이콘 파일명 목록
  event.items  : 점수 항목 [{name, points(1단위당 점수)}]
  event.custom : True면 유저가 항목/배점을 직접 추가하는 커스텀 이벤트

새 이벤트 추가 = 아래 EVENT_GROUPS 데이터에 항목 추가하면 끝.
"""
APP_TITLE = "WOS 이벤트 계산기"
BASE_TIME = 9 * 60  # AM 9:00 = 540분 (시간 페이지 기본값, 코드 고정)


def _placeholder(name, icon=None):
    """아직 내용 미정인 자리표시용 이벤트."""
    return {
        "name": name,
        "icon": icon,
        "rewards": [],
        "items": [{"name": "(행동 미정)", "points": 0}],
    }


def _day(label, items, defaults=None):
    """멀티데이 이벤트의 하루 분 (날짜라벨, [(항목명, 배점), ...], 현재/목표 초기값)."""
    return {
        "label": label,
        "items": [{"name": n, "points": p} for n, p in items],
        "defaults": defaults or {},
    }


def _multiday_event(name, days, icon=None, rewards=None):
    """날짜별로 항목이 다른 이벤트(예: 연맹 대작전 6일). days = [_day(...), ...]."""
    return {
        "name": name,
        "icon": icon,
        "rewards": rewards or [],
        "days": days,
    }


def _event(name, items, icon=None, rewards=None, defaults=None):
    """(이름, [(항목명, 기본배점), ...], 사이드바 아이콘, 보상 아이콘 목록) -> 이벤트 dict.

    defaults: 현재/목표 점수의 초기값 {"current": "0", "target": "20000"} (저장값 없을 때만 사용).
    """
    return {
        "name": name,
        "icon": icon,
        "rewards": rewards or [],
        "items": [{"name": n, "points": p} for n, p in items],
        "defaults": defaults or {},
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
                ("제련된 불의 수정", 1500),
                ("영주 장비", 3),
                ("레어 영웅 파편", 15),
                ("에픽 영웅 파편", 50),
                ("레전드 영웅 파편", 125),
                ("가속 사용", 1),
                ("전문가 표식", 200),
                ("학문의 책", 2),
            ], icon="icon_arms.png", rewards=[
                "icon_diamond.png",
                "icon_legend_charm_part.png",
                "icon_design_plan.png",
                "icon_legend_skillbook.png",
            ], defaults={"current": "0", "target": "20000"}),
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
            {
                "name": "Custom",
                "icon": "icon_custom.png",
                "rewards": [],
                "items": [],
                "custom": True,  # 유저가 항목/배점을 직접 추가
            },
        ],
    },
    {
        "name": "연맹 이벤트",
        "events": [
            _placeholder("최강 왕국"),
            _multiday_event("연맹 대작전", [
                _day("I", [
                    ("행상 호송", 10000),
                    ("행상 약탈", 10000),
                    ("제련된 불의 수정", 18750),
                    ("불의 수정", 1250),
                    ("불의 수정 조각", 625),
                    ("가속 사용", 18),
                    ("생고기 2000개 채집", 2),
                    ("목재 2000개 채집", 2),
                    ("석탄 400개 채집", 2),
                    ("철광 100개 채집", 2),
                    ("다이아1개 소모", 1),
                    ("전문가 표식", 3600),
                    ("학문의 책", 36),
                ]),
                _day("II", [
                    ("행상 호송", 10000),
                    ("행상 약탈", 10000),
                    ("레어 영웅 파편", 210),
                    ("에픽 영웅 파편", 750),
                    ("레전드 영웅 파편", 1875),
                    ("제련된 불의 수정", 18750),
                    ("불의 수정", 1250),
                    ("불의 수정 조각", 625),
                    ("가속 사용", 18),
                    ("다이아1개 소모", 1),
                    ("전문가 표식", 3600),
                    ("학문의 책", 36),
                ]),
                _day("III", [("(항목 미정)", 0)]),
                _day("IV", [("(항목 미정)", 0)]),
                _day("V", [("(항목 미정)", 0)]),
                _day("VI", [("(항목 미정)", 0)]),
            ]),
            _placeholder("빙원의 왕"),
            _placeholder("연맹 총동원"),
        ],
    },
]

# 저장/복원용 안정적인 키 부여 ("그룹명::이벤트명")
for _group in EVENT_GROUPS:
    for _ev in _group["events"]:
        _ev["_key"] = f'{_group["name"]}::{_ev["name"]}'


_ITEM_COL_MIN = None


def item_col_minsize():
    """모든 이벤트의 항목명 중 가장 긴 폭(px). 4개 메뉴의 컬럼 정렬을 통일하기 위함."""
    global _ITEM_COL_MIN
    if _ITEM_COL_MIN is None:
        import tkinter.font as tkfont
        f = tkfont.Font(font=("Segoe UI", 10))
        widest = 0
        for group in EVENT_GROUPS:
            for ev in group["events"]:
                # 일반 이벤트는 items, 멀티데이 이벤트는 days[].items
                item_lists = [ev["items"]] if "items" in ev else \
                    [d["items"] for d in ev.get("days", [])]
                for items in item_lists:
                    for it in items:
                        widest = max(widest, f.measure(it["name"]))
        _ITEM_COL_MIN = widest + 12
    return _ITEM_COL_MIN
