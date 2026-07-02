"""otak/chat.py — OpenAI API integration. Status: Phase 3 — stub."""

from config import ChatConfig


class ChatEngine:  # Phase 3
    def __init__(self, config: ChatConfig):
        pass

    def chat(self, prompt: str, context: dict) -> str:
        return ""

    def clear_memory(self) -> None:
        pass
