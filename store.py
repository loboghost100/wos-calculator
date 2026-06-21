"""사용자 입력값 저장소 (JSON)."""
import json

from resources import data_file


class Store:
    """사용자 입력값을 JSON으로 저장/복원."""

    def __init__(self):
        self.path = data_file()
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
