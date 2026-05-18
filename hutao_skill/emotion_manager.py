"""心境状态管理器 v3.0

支持 SFW/NSFW 双模式心境状态管理。
"""

import json
import logging
import os
import random
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EmotionState:
    """心境状态"""
    name: str
    name_en: str
    name_ja: str
    keywords: List[str]
    emotion_tags: List[str]

    def get_localized_name(self, lang: str = "zh") -> str:
        if lang == "en":
            return self.name_en
        elif lang == "ja":
            return self.name_ja
        return self.name


class EmotionManager:
    """心境状态管理器（双模式支持）"""

    def __init__(self, config_path: Optional[str] = None, mode: str = "sfw"):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config.json")
        self._mode = mode
        self._states: Dict[str, EmotionState] = {}
        self._load_config()

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        if value != self._mode:
            self._mode = value
            self._states.clear()
            self._load_config()
            logger.info(f"EmotionManager mode switched to: {value}")

    def _load_config(self) -> None:
        if not os.path.exists(self.config_path):
            logger.error(f"Config file not found: {self.config_path}")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise

        states_key = f"{self._mode}_emotion_states"
        states_config = config.get(states_key, {})

        for state_name, state_data in states_config.items():
            self._states[state_name] = EmotionState(
                name=state_name,
                name_en=state_data.get("name_en", state_name),
                name_ja=state_data.get("name_ja", state_name),
                keywords=state_data.get("keywords", []),
                emotion_tags=state_data.get("emotion_tags", []),
            )

        logger.info(f"Loaded {len(self._states)} emotion states for mode '{self._mode}'")

    def get_all_states(self) -> List[str]:
        return list(self._states.keys())

    def get_state(self, name: str) -> Optional[EmotionState]:
        return self._states.get(name)

    def detect_emotion(self, message: str) -> Optional[str]:
        scores: Dict[str, int] = {}
        message_lower = message.lower()

        for state_name, state in self._states.items():
            score = 0
            for kw in state.keywords:
                if kw.lower() in message_lower:
                    score += 1
            if score > 0:
                scores[state_name] = score

        if not scores:
            return None

        best_state = max(scores, key=scores.get)
        logger.debug(f"Detected emotion '{best_state}' for message (score: {scores[best_state]})")
        return best_state

    def get_state_stats_display(self, state_name: str, lang: str = "zh") -> str:
        state = self.get_state(state_name)
        if not state:
            return ""

        localized_name = state.get_localized_name(lang)
        tags = ", ".join(state.emotion_tags)
        keywords = ", ".join(state.keywords[:5])

        return (
            f"**{localized_name}**\n"
            f"🏷️ 标签: {tags}\n"
            f"🔑 关键词: {keywords}..."
        )

    def get_random_state(self, exclude: Optional[str] = None) -> str:
        states = self.get_all_states()
        if exclude and exclude in states:
            states = [s for s in states if s != exclude]
        return random.choice(states) if states else "引魂"

    def reload(self) -> None:
        self._states.clear()
        self._load_config()
