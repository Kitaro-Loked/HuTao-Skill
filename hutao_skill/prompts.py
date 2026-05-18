"""提示词加载器 v3.0

支持 SFW/NSFW 双模式提示词加载，带缓存和热重载。
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_prompts_data: Optional[dict] = None
_prompts_path: Optional[str] = None


def _load_prompts() -> dict:
    global _prompts_data, _prompts_path
    if _prompts_path is None:
        _prompts_path = os.path.join(os.path.dirname(__file__), "prompts.json")
    if not os.path.exists(_prompts_path):
        logger.error(f"Prompts file not found: {_prompts_path}")
        return {}
    try:
        with open(_prompts_path, "r", encoding="utf-8") as f:
            _prompts_data = json.load(f)
        logger.debug("Prompts loaded successfully")
        return _prompts_data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in prompts file: {e}")
        return {}


def _get_prompts() -> dict:
    global _prompts_data
    if _prompts_data is None:
        _prompts_data = _load_prompts()
    return _prompts_data


def get_system_prompt(lang: str = "zh", mode: str = "sfw") -> str:
    prompts = _get_prompts()
    key = f"{mode}_system_prompts"
    system_prompts = prompts.get(key, {})
    return system_prompts.get(lang, system_prompts.get("zh", ""))


def get_emotion_state_addition(emotion: str, lang: str = "zh", mode: str = "sfw") -> str:
    prompts = _get_prompts()
    key = f"{mode}_emotion_states"
    emotion_states = prompts.get(key, {})
    state = emotion_states.get(emotion, {})
    additions = state.get("system_prompt_addition", {})
    return additions.get(lang, additions.get("zh", ""))


def get_emotion_state_keywords(emotion: str, mode: str = "sfw") -> list:
    prompts = _get_prompts()
    key = f"{mode}_emotion_states"
    emotion_states = prompts.get(key, {})
    state = emotion_states.get(emotion, {})
    return state.get("trigger_keywords", [])


def get_emotion_state_name(emotion: str, lang: str = "zh", mode: str = "sfw") -> str:
    prompts = _get_prompts()
    key = f"{mode}_emotion_states"
    emotion_states = prompts.get(key, {})
    state = emotion_states.get(emotion, {})
    names = state.get("name", {})
    return names.get(lang, names.get("zh", emotion))


def get_all_emotion_states(mode: str = "sfw") -> list:
    prompts = _get_prompts()
    key = f"{mode}_emotion_states"
    return list(prompts.get(key, {}).keys())


def get_error_message(lang: str = "zh") -> str:
    prompts = _get_prompts()
    common = prompts.get("common", {})
    errors = common.get("error_messages", {})
    return errors.get(lang, errors.get("zh", ""))


def get_memory_cleared_message(lang: str = "zh") -> str:
    prompts = _get_prompts()
    common = prompts.get("common", {})
    msgs = common.get("memory_cleared", {})
    return msgs.get(lang, msgs.get("zh", ""))


def reload_prompts() -> None:
    global _prompts_data
    _prompts_data = None
    _load_prompts()
    logger.info("Prompts reloaded")
