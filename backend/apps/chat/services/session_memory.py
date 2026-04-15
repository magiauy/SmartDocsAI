from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock


class SessionMemoryStore:
    _lock = Lock()
    _sessions: dict[str, deque] = defaultdict(deque)

    def __init__(self, max_turns: int = 8):
        self.max_turns = max(1, int(max_turns))
        self.max_messages = self.max_turns * 2

    def get_history(self, session_id: str | int) -> list[dict]:
        key = str(session_id)
        with self._lock:
            history = self._sessions.get(key, deque())
            return list(history)

    def append_turn(self, session_id: str | int, user_message: str, assistant_message: str):
        key = str(session_id)
        with self._lock:
            history = self._sessions.setdefault(key, deque(maxlen=self.max_messages))
            if history.maxlen != self.max_messages:
                history = deque(history, maxlen=self.max_messages)
                self._sessions[key] = history
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": assistant_message})

    def set_history(self, session_id: str | int, messages: list[dict]):
        key = str(session_id)
        trimmed = messages[-self.max_messages :]
        with self._lock:
            self._sessions[key] = deque(trimmed, maxlen=self.max_messages)

    def clear_session(self, session_id: str | int):
        key = str(session_id)
        with self._lock:
            self._sessions.pop(key, None)
