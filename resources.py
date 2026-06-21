"""파일 경로 / 입력 검증 등 공용 헬퍼."""
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


def comma_format(var):
    """StringVar 값을 '숫자만 + 천단위 콤마' 정수 표기로 정규화.
    값이 바뀌면 var.set() 후 True 반환(트레이스 재진입으로 recalc 처리)."""
    digits = "".join(c for c in var.get() if c.isdigit())
    formatted = f"{int(digits):,}" if digits else ""
    if formatted != var.get():
        var.set(formatted)
        return True
    return False


def to_num(s):
    """문자열(콤마 포함 가능)을 float으로. 실패 시 0."""
    try:
        return float(str(s).replace(",", "").strip() or 0)
    except ValueError:
        return 0
