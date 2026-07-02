"""otak/memory.py — Conversation memory. Status: Phase 3 — stub."""


class ConversationMemory:  # Phase 3
    def __init__(self, max_history: int = 20):
        pass

    def add(self, role: str, content: str) -> None:
        pass

    def history(self) -> list:
        return []

    def clear(self) -> None:
        pass
