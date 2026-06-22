"""파일 경로 / 입력 검증 등 공용 헬퍼."""
import math
import os
import sys


def data_file():
    """사용자 데이터(userdata.json) 경로.
    저장 위치: 실행 파일(.exe)과 같은 폴더 (개발 중 .py 실행 시엔 스크립트 폴더).
    """
    if getattr(sys, "frozen", False):       # PyInstaller로 빌드된 .exe
        base = os.path.dirname(sys.executable)
    else:                                   # 일반 .py 실행
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "userdata.json")


def resource(*parts):
    """번들된 리소스 경로 (PyInstaller는 임시폴더 _MEIPASS에 풀어둠).
    예: resource("assets", "icon.ico")
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def is_number(proposed):
    """Entry 입력 검증: 빈 값 또는 숫자(소수점 1개 허용)만 True."""
    if proposed == "":
        return True
    return proposed.count(".") <= 1 and all(c.isdigit() or c == "." for c in proposed)


def _group_digits(digits):
    """숫자 문자열에 천단위 콤마만 삽입(정수 변환 없이 앞자리 0 유지). 빈 문자열은 그대로."""
    if not digits:
        return ""
    parts = []
    while len(digits) > 3:
        parts.insert(0, digits[-3:])
        digits = digits[:-3]
    parts.insert(0, digits)
    return ",".join(parts)


def comma_format(var):
    """StringVar 값을 '숫자만 + 천단위 콤마'로 정규화 (앞자리 0 유지 — 편집 중 자리 보존).
    예: '300,000'에서 앞 3을 지워 '00,000'이 돼도 0으로 무너지지 않음.
    값이 바뀌면 var.set() 후 True 반환(트레이스 재진입으로 recalc 처리)."""
    digits = "".join(c for c in var.get() if c.isdigit())
    formatted = _group_digits(digits)
    if formatted != var.get():
        var.set(formatted)
        return True
    return False


def comma_normalize(var):
    """앞자리 0 정리 후 콤마 재포맷 (입력칸에서 포커스가 벗어날 때 호출).
    전부 0이면 '0', 빈 값이면 '' 로 정리."""
    digits = "".join(c for c in var.get() if c.isdigit())
    if digits == "":
        normalized = ""
    else:
        stripped = digits.lstrip("0")
        normalized = stripped if stripped else "0"
    formatted = _group_digits(normalized)
    if formatted != var.get():
        var.set(formatted)


def to_num(s):
    """문자열(콤마 포함 가능)을 float으로. 실패 시 0."""
    try:
        return float(str(s).replace(",", "").strip() or 0)
    except ValueError:
        return 0


def gap_text(target, current):
    """현재/목표 점수로 안내 문구 생성 (일반/커스텀 이벤트 공용)."""
    gap = target - current
    if target <= 0:
        return "목표 점수를 입력하세요."
    if gap <= 0:
        return f"이미 목표 달성! ({int(-gap):,} 점 초과)"
    return f"필요 점수 (목표 - 현재): {int(gap):,} 점"


def need_text(gap, target, points):
    """항목별 필요 수량 문구 (points는 실효 배점). 일반/커스텀 이벤트 공용."""
    if target <= 0 or gap <= 0:
        return "0개" if (gap <= 0 and target > 0) else "-"
    if points <= 0:
        return "—"
    return f"{math.ceil(gap / points):,}개"
