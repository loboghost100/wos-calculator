"""앱 상수 + 이벤트 데이터 정의.

이벤트 데이터 (그룹 -> 이벤트):
  group.name   : 사이드바 상위 항목(펼쳐지는 그룹)
  event.name   : 하위 항목(클릭 시 오른쪽에 계산기 표시)
  event.icon   : 사이드바 아이콘 파일명 (assets/ 기준)
  event.rewards: 타이틀 옆 보상 아이콘 파일명 목록
  event.items  : 점수 항목 [{name, points(1단위당 점수)}]
  event.custom : True면 유저가 항목/배점을 직접 추가하는 커스텀 이벤트

새 이벤트 추가 = 아래 EVENT_GROUPS 데이터에 항목 추가하면 끝.
항목명은 Item 네임스페이스(아래)로 관리 — 오타/이름변경은 거기 한 곳만 고치면
개인/연맹 전 이벤트에 동일하게 반영된다.
"""
APP_TITLE = "WOS 이벤트 계산기"
BASE_TIME = 9 * 60  # AM 9:00 = 540분 (시간 페이지 기본값, 코드 고정)


class Item:
    """항목명 단일 출처(SSOT).

    같은 항목이 개인/연맹 여러 이벤트에 반복 등장하므로, 표기를 여기서만 정의해
    중복·불일치(예: '다이아1개 소모' vs '다이아 1개 소모')를 원천 차단한다.
    값(문자열)을 바꾸면 전 이벤트에 반영된다.
    """
    ESCORT          = "행상 호송"
    RAID            = "행상 약탈"
    REFINED_FC      = "제련된 불의 수정"
    FIRE_CRYSTAL    = "불의 수정"
    FC_FRAGMENT     = "불의 수정 조각"
    SPEEDUP         = "가속 사용"
    DIAMOND         = "다이아1개 소모"
    EXPERT_MARK     = "전문가 표식"
    SKILL_BOOK      = "학문의 책"
    LORD_GEAR       = "영주 장비"
    LORD_GEM        = "영주 보석"
    HERO_RARE       = "레어 영웅 파편"
    HERO_EPIC       = "에픽 영웅 파편"
    HERO_LEGEND     = "레전드 영웅 파편"
    MASTERY_STONE   = "마스터리석"
    MITHRIL         = "미스릴"
    EXCLUSIVE_GEAR  = "전용 장비"
    TROOP_TRAIN_10  = "10급 병사 훈련"
    TROOP_TRAIN_11  = "11급 병사 훈련"
    PET_BREAK       = "펫 돌파"
    WILD_MARK_HIGH  = "고급 야성의 표식"
    WILD_MARK_NORMAL = "일반 야성의 표식"
    GATHER_MEAT     = "생고기 2000개 채집"
    GATHER_WOOD     = "목재 2000개 채집"
    GATHER_COAL     = "석탄 400개 채집"
    GATHER_IRON     = "철광 100개 채집"
    TBD             = "(항목 미정)"       # 항목 미정 자리표시
    ACTION_TBD      = "(행동 미정)"       # 이벤트 자체 미정 자리표시


def _placeholder(name, icon=None):
    """아직 내용 미정인 자리표시용 이벤트 (편집 비활성 = 읽기전용)."""
    return {
        "name": name,
        "icon": icon,
        "rewards": [],
        "items": [{"name": Item.ACTION_TBD, "points": 0}],
        "editable": False,
    }


def _day(label, items, defaults=None):
    """멀티데이 이벤트의 하루 분 (날짜라벨, [(항목명, 배점), ...], 현재/목표 초기값)."""
    return {
        "label": label,
        "items": [{"name": n, "points": p} for n, p in items],
        "defaults": defaults or {},
    }


def _multiday_event(name, days, icon=None, rewards=None, bonus=False, editable=False, scale=1.0):
    """날짜별로 항목이 다른 이벤트(예: 연맹 대작전 6일). days = [_day(...), ...].

    bonus:    True면 페이지에 '전문가의 도움'(배점 보너스 %) 입력칸을 둔다.
    editable: True면 각 날짜를 보기/편집 토글로 유저가 항목·배점을 직접 관리한다.
    scale:    모든 날짜 항목 배점에 곱할 배율 (예: 1.5 = 기본 배점 +50% 적용).
    """
    if scale != 1.0:
        for d in days:
            for it in d["items"]:
                it["points"] = it["points"] * scale
    return {
        "name": name,
        "icon": icon,
        "rewards": rewards or [],
        "days": days,
        "bonus": bonus,
        "editable": editable,
    }


def _custom_days(labels):
    """라벨 목록 -> 빈 날짜 목록 (항목은 편집 모드에서 유저가 추가, userdata 로드)."""
    return [_day(lbl, []) for lbl in labels]


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
        "editable": True,   # 보기/편집 토글 (기본값은 두고 유저가 수정 가능)
    }


def _tbd_days(labels):
    """라벨 목록 -> 항목 미정 멀티데이 일자 목록."""
    return [_day(lbl, [(Item.TBD, 0)]) for lbl in labels]


EVENT_GROUPS = [
    {
        "name": "시간",
        "events": [],  # 이벤트가 아닌 별개 기능 -> 하위 항목 없이 단독 버튼
    },
    {
        "name": "개인 이벤트",
        "events": [
            _event("군비 경쟁1", [
                (Item.FIRE_CRYSTAL, 100),
                (Item.FC_FRAGMENT, 50),
                (Item.REFINED_FC, 1500),
                (Item.LORD_GEAR, 3),
                (Item.HERO_RARE, 15),
                (Item.HERO_EPIC, 50),
                (Item.HERO_LEGEND, 125),
                (Item.SPEEDUP, 1),
                (Item.EXPERT_MARK, 200),
                (Item.SKILL_BOOK, 2),
            ], icon="icon_arms.png", rewards=[
                "icon_diamond.png",
                "icon_legend_charm_part.png",
                "icon_design_plan.png",
                "icon_legend_skillbook.png",
            ], defaults={"current": "0", "target": "20000"}),
            _event("군비 경쟁2", [
                (Item.FIRE_CRYSTAL, 100),
                (Item.FC_FRAGMENT, 50),
                (Item.REFINED_FC, 1500),
                (Item.LORD_GEAR, 3),
                (Item.MASTERY_STONE, 30),
                (Item.MITHRIL, 10),
                (Item.EXCLUSIVE_GEAR, 5),
                (Item.SPEEDUP, 1),
            ], icon="icon_arms.png", rewards=[
                "icon_diamond.png",
                "icon_legend_charm_part.png",
                "icon_legend_skillbook.png",
                "icon_legend_explore_skillbook.png",
            ]),
            _event("사관의 계획1", [
                (Item.LORD_GEM, 50),
                (Item.MASTERY_STONE, 30),
                (Item.EXCLUSIVE_GEAR, 5),
                (Item.TROOP_TRAIN_10, 1),
                (Item.TROOP_TRAIN_11, 1),
            ], icon="icon_saquan.png", rewards=[
                "icon_diamond.png",
                "icon_legend_charm_part.png",
                "icon_mastery_stone.png",
                "icon_legend_skillbook.png",
            ]),
            _event("사관의 계획2", [
                (Item.LORD_GEAR, 3),
                (Item.HERO_RARE, 15),
                (Item.HERO_EPIC, 50),
                (Item.HERO_LEGEND, 125),
                (Item.MASTERY_STONE, 30),
                (Item.EXCLUSIVE_GEAR, 5),
                (Item.MITHRIL, 10),
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
            _multiday_event("최강 왕국", _custom_days(["I", "II", "III", "IV", "V"]),
                            icon="icon_svs.png", editable=True),
            _multiday_event("연맹 대작전", [
                _day("I", [
                    (Item.ESCORT, 10000),
                    (Item.RAID, 10000),
                    (Item.REFINED_FC, 18750),
                    (Item.FIRE_CRYSTAL, 1250),
                    (Item.FC_FRAGMENT, 625),
                    (Item.SPEEDUP, 18),
                    (Item.GATHER_MEAT, 2),
                    (Item.GATHER_WOOD, 2),
                    (Item.GATHER_COAL, 2),
                    (Item.GATHER_IRON, 2),
                    (Item.DIAMOND, 1),
                    (Item.EXPERT_MARK, 3600),
                    (Item.SKILL_BOOK, 36),
                ]),
                _day("II", [
                    (Item.ESCORT, 10000),
                    (Item.RAID, 10000),
                    (Item.HERO_RARE, 210),
                    (Item.HERO_EPIC, 750),
                    (Item.HERO_LEGEND, 1875),
                    (Item.REFINED_FC, 18750),
                    (Item.FIRE_CRYSTAL, 1250),
                    (Item.FC_FRAGMENT, 625),
                    (Item.SPEEDUP, 18),
                    (Item.DIAMOND, 1),
                    (Item.EXPERT_MARK, 3600),
                    (Item.SKILL_BOOK, 36),
                ]),
                _day("III", [
                    (Item.ESCORT, 10000),
                    (Item.RAID, 10000),
                    (Item.LORD_GEM, 45),
                    (Item.PET_BREAK, 30),
                    (Item.WILD_MARK_HIGH, 9370),
                    (Item.WILD_MARK_NORMAL, 680),
                    (Item.GATHER_MEAT, 2),
                    (Item.GATHER_WOOD, 2),
                    (Item.GATHER_COAL, 2),
                    (Item.GATHER_IRON, 2),
                    (Item.DIAMOND, 1),
                ]),
                _day("IV", [
                    (Item.ESCORT, 10000),
                    (Item.RAID, 10000),
                    (Item.LORD_GEM, 45),
                    (Item.MASTERY_STONE, 1875),
                    (Item.EXCLUSIVE_GEAR, 3750),
                    (Item.MITHRIL, 67500),
                    (Item.TROOP_TRAIN_10, 24),
                    (Item.TROOP_TRAIN_11, 30),
                    (Item.DIAMOND, 1),
                ]),
                _day("V", [
                    (Item.ESCORT, 10000),
                    (Item.RAID, 10000),
                    (Item.LORD_GEAR, 22),
                    (Item.REFINED_FC, 18750),
                    (Item.FIRE_CRYSTAL, 1250),
                    (Item.FC_FRAGMENT, 625),
                    (Item.SPEEDUP, 18),
                    (Item.DIAMOND, 1),
                ]),
                _day("VI", [
                    (Item.ESCORT, 10000),
                    (Item.RAID, 10000),
                    (Item.LORD_GEAR, 22),
                    (Item.LORD_GEM, 45),
                    (Item.MASTERY_STONE, 1875),
                    (Item.EXCLUSIVE_GEAR, 3750),
                    (Item.MITHRIL, 67500),
                    (Item.HERO_RARE, 210),
                    (Item.HERO_EPIC, 750),
                    (Item.HERO_LEGEND, 1875),
                    (Item.PET_BREAK, 30),
                    (Item.WILD_MARK_HIGH, 9370),
                    (Item.WILD_MARK_NORMAL, 680),
                    (Item.REFINED_FC, 18750),
                    (Item.FIRE_CRYSTAL, 1250),
                    (Item.FC_FRAGMENT, 625),
                    (Item.SPEEDUP, 18),
                    (Item.DIAMOND, 1),
                ]),
            ], icon="icon_alliance_operation.png", scale=1.5, editable=True),
            _multiday_event("빙원의 왕", _custom_days(["I", "II", "III", "IV", "V", "VI", "VII"]),
                            icon="icon_frostfire_king.png", editable=True),
            {
                "name": "연맹 총동원",
                "icon": "icon_alliance_mobilization.png",
                "training": True,  # 훈련 계획 계산기 (전투력 목표)
            },
            {
                "name": "Custom",
                "icon": "icon_news.png",
                "rewards": [],
                "days": [],          # 동적: 유저가 탭 개수를 지정
                "editable": True,
                "dynamic": True,
            },
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
