# WOS 이벤트 계산기

White Out Survival(WOS) 게임의 이벤트 목표 점수 달성에 필요한 아이템 수량을 계산해주는 Windows 데스크톱 앱입니다.

현재 점수와 목표 점수를 입력하면, 각 아이템을 **몇 개 써야 목표를 채우는지** 자동으로 계산해줍니다.

## 주요 기능

- 🕘 **시간** — 현재 PC 시간 기준으로 등록한 시각까지 남은 시간 계산 (12h/24h 전환, 시각 추가/삭제)
- 📋 **개인 이벤트** — 군비 경쟁 1·2, 사관의 계획 1·2
  - 현재/목표 점수 입력 → 항목별 필요 수량 자동 계산
  - 배점은 유저가 직접 수정 가능 (천단위 콤마 자동, 숫자만 입력)
- 🔧 **Custom** — 항목·배점을 유저가 직접 추가/삭제하는 커스텀 계산기 (제목 지정 가능)
- 🤝 **연맹 이벤트** — 최강 왕국 / 연맹 대작전 / 빙원의 왕 / 연맹 총동원 (준비 중)
- 💾 모든 입력값은 실행 파일과 같은 폴더의 `userdata.json`에 자동 저장 → 껐다 켜도 유지

## 설치 / 실행

[Releases](https://github.com/loboghost100/wos-calculator/releases)에서 최신 `WOS-Calculator.zip`을 받아 압축을 풀고 `WOS-Calculator.exe`를 실행하세요. 파이썬 설치는 필요 없습니다.

> ⚠️ 서명되지 않은 실행 파일이라 Windows의 **스마트 앱 컨트롤(SmartScreen)**이 차단할 수 있습니다. 신뢰할 수 있는 경우 "추가 정보 → 실행"으로 진행하세요.

## 개발

```bash
# 의존성 (빌드 시에만 필요)
py -m pip install pyinstaller

# 소스 실행
py main.py

# 단일 exe 빌드
py -m PyInstaller --onefile --windowed --name "WOS-Calculator" --icon "assets/icon.ico" --add-data "assets;assets" main.py --noconfirm
```

빌드 결과물은 `dist/WOS-Calculator.exe`에 생성됩니다.

## 자동 릴리스

`v`로 시작하는 태그를 push하면 GitHub Actions가 자동으로 exe를 빌드하고 zip으로 압축해 릴리스에 첨부합니다.

```bash
git tag v0.4.0
git push origin v0.4.0
```

## 프로젝트 구조

| 파일 | 역할 |
|------|------|
| `main.py` | 진입점 (App) |
| `config.py` | 상수 + 이벤트 데이터(`EVENT_GROUPS`) |
| `resources.py` | 경로/입력 검증/콤마 포맷 등 공용 헬퍼 |
| `store.py` | 사용자 데이터 저장소(JSON) |
| `sidebar.py` | 좌측 버튼형 아코디언 사이드바 |
| `event_calc.py` | 일반 이벤트 계산기 (군비/사관) |
| `custom_calc.py` | 커스텀 이벤트 계산기 |
| `time_page.py` | 시간 페이지 |
| `assets/` | 아이콘 리소스 |

새 이벤트는 `config.py`의 `EVENT_GROUPS`에 항목을 추가하면 됩니다.
