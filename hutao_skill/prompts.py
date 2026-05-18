"""提示词加载器

支持从 prompts.json 加载系统提示词和心境状态追加内容。
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# 全局缓存
_prompts_data: Optional[dict] = None
_prompts_path: Optional[str] = None


def _load_prompts() -> dict:
    """加载提示词配置"""
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
    """获取提示词数据（带缓存）"""
    global _prompts_data
    if _prompts_data is None:
        _prompts_data = _load_prompts()
    return _prompts_data


def get_system_prompt(lang: str = "zh") -> str:
    """获取系统提示词"""
    prompts = _get_prompts()
    system_prompts = prompts.get("system_prompts", {})
    return system_prompts.get(lang, system_prompts.get("zh", ""))


def get_emotion_state_addition(emotion: str, lang: str = "zh") -> str:
    """获取心境状态追加提示词"""
    prompts = _get_prompts()
    emotion_states = prompts.get("emotion_states", {})
    state = emotion_states.get(emotion, {})
    additions = state.get("system_prompt_addition", {})
    return additions.get(lang, additions.get("zh", ""))


def get_emotion_state_keywords(emotion: str) -> list:
    """获取心境状态触发关键词"""
    prompts = _get_prompts()
    emotion_states = prompts.get("emotion_states", {})
    state = emotion_states.get(emotion, {})
    return state.get("trigger_keywords", [])


def get_emotion_state_name(emotion: str, lang: str = "zh") -> str:
    """获取心境状态本地化名称"""
    prompts = _get_prompts()
    emotion_states = prompts.get("emotion_states", {})
    state = emotion_states.get(emotion, {})
    names = state.get("name", {})
    return names.get(lang, names.get("zh", emotion))


def get_all_emotion_states() -> list:
    """获取所有心境状态名称"""
    prompts = _get_prompts()
    return list(prompts.get("emotion_states", {}).keys())


def reload_prompts() -> None:
    """重新加载提示词（热重载）"""
    global _prompts_data
    _prompts_data = None
    _load_prompts()
    logger.info("Prompts reloaded")
