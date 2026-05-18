"""情感记忆系统：记录与用户的互动历史

v1.0 特性：
- 自动清理机制（按时间和数量）
- 记忆条目最大年龄限制
- 支持清理间隔配置
- 胡桃风格的日记生成
"""

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """单条记忆条目"""

    timestamp: str
    user_message: str
    bot_response: str
    form: str
    emotion_score: float = 0.0
    keywords: List[str] = field(default_factory=list)
    context_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        return cls(**data)

    @property
    def timestamp_dt(self) -> datetime:
        """获取 timestamp 的 datetime 对象"""
        try:
            return datetime.fromisoformat(self.timestamp)
        except ValueError:
            return datetime.now()

    @property
    def age_seconds(self) -> float:
        """获取记忆条目的年龄（秒）"""
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return (datetime.now() - dt).total_seconds()
        except ValueError:
            return 0.0


class EmotionMemory:
    """情感记忆管理器"""

    def __init__(
        self,
        max_entries: int = 50,
        storage_path: Optional[str] = None,
        auto_cleanup: bool = True,
        cleanup_interval: int = 86400,
        max_age_days: int = 7,
    ):
        self.max_entries = max_entries
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), "data", "memory.json"
        )
        self.auto_cleanup = auto_cleanup
        self.cleanup_interval = cleanup_interval
        self.max_age_days = max_age_days
        self._memories: List[MemoryEntry] = []
        self._user_preferences: Dict[str, Any] = {}
        self._last_cleanup = 0.0
        self._load()

    def _load(self) -> None:
        """从文件加载记忆"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._memories = [
                        MemoryEntry.from_dict(entry)
                        for entry in data.get("memories", [])
                    ]
                    self._user_preferences = data.get("preferences", {})
                    self._last_cleanup = data.get("last_cleanup", 0)
                logger.info(f"Loaded {len(self._memories)} memories from {self.storage_path}")
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Failed to load memories: {e}. Starting fresh.")
                self._memories = []
                self._user_preferences = {}
                self._last_cleanup = 0

        if self.auto_cleanup:
            self._auto_cleanup()

    def save(self) -> None:
        """保存记忆到文件"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data = {
            "memories": [entry.to_dict() for entry in self._memories],
            "preferences": self._user_preferences,
            "last_updated": datetime.now().isoformat(),
            "last_cleanup": self._last_cleanup,
        }
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {len(self._memories)} memories")
        except OSError as e:
            logger.error(f"Failed to save memories: {e}")

    def _auto_cleanup(self) -> None:
        """自动清理过期记忆"""
        now = time.time()
        if now - self._last_cleanup < self.cleanup_interval:
            return

        original_count = len(self._memories)
        max_age_seconds = self.max_age_days * 86400

        self._memories = [
            m for m in self._memories if m.age_seconds < max_age_seconds
        ]

        if len(self._memories) > self.max_entries:
            self._memories = self._memories[-self.max_entries :]

        removed = original_count - len(self._memories)
        if removed > 0:
            logger.info(f"Auto cleanup removed {removed} old memories, remaining {len(self._memories)}")

        self._last_cleanup = now
        if removed > 0:
            self.save()

    def add(
        self,
        user_message: str,
        bot_response: str,
        form: str,
        emotion_score: float = 0.0,
        keywords: Optional[List[str]] = None,
        context_summary: str = "",
    ) -> None:
        """添加一条新记忆"""
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            user_message=user_message,
            bot_response=bot_response,
            form=form,
            emotion_score=emotion_score,
            keywords=keywords or [],
            context_summary=context_summary,
        )
        self._memories.append(entry)

        if len(self._memories) > self.max_entries:
            self._memories = self._memories[-self.max_entries :]

        if self.auto_cleanup:
            self._auto_cleanup()

        self.save()

    def get_recent(self, n: int = 5) -> List[MemoryEntry]:
        """获取最近 n 条记忆"""
        return self._memories[-n:] if self._memories else []

    def get_relevant_memories(self, query: str, top_k: int = 3) -> List[MemoryEntry]:
        """基于关键词获取相关记忆"""
        query_keywords = set(query.lower().split())
        scored = []
        for entry in self._memories:
            score = 0
            entry_text = f"{entry.user_message} {entry.bot_response} {entry.context_summary}".lower()
            for kw in query_keywords:
                if kw in entry_text:
                    score += 1
            if entry.keywords:
                for kw in entry.keywords:
                    if kw.lower() in query.lower():
                        score += 2
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:top_k]]

    def get_memory_summary(self) -> str:
        """生成记忆摘要，用于注入系统提示词"""
        if not self._memories:
            return ""
        recent = self.get_recent(3)
        lines = ["[Recent Memories]"]
        for entry in recent:
            lines.append(
                f"- [{entry.form}] User: {entry.user_message[:50]}... "
                f"You responded: {entry.bot_response[:50]}..."
            )
        return "\n".join(lines)

    def get_emotion_trend(self) -> float:
        """获取近期情感趋势"""
        if not self._memories:
            return 0.0
        recent = self.get_recent(10)
        if not recent:
            return 0.0
        return sum(entry.emotion_score for entry in recent) / len(recent)

    def get_form_frequency(self) -> Dict[str, int]:
        """统计各心境出现频率"""
        freq: Dict[str, int] = {}
        for entry in self._memories:
            freq[entry.form] = freq.get(entry.form, 0) + 1
        return freq

    def set_preference(self, key: str, value: Any) -> None:
        """设置用户偏好"""
        self._user_preferences[key] = value
        self.save()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """获取用户偏好"""
        return self._user_preferences.get(key, default)

    def clear(self) -> None:
        """清空所有记忆"""
        self._memories = []
        self._user_preferences = {}
        self._last_cleanup = time.time()
        self.save()
        logger.info("All memories cleared")

    def cleanup_old_memories(self, max_age_days: Optional[int] = None) -> int:
        """手动清理过期记忆"""
        max_age = (max_age_days or self.max_age_days) * 86400
        original_count = len(self._memories)
        self._memories = [m for m in self._memories if m.age_seconds < max_age]
        removed = original_count - len(self._memories)
        if removed > 0:
            self._last_cleanup = time.time()
            self.save()
            logger.info(f"Manual cleanup removed {removed} old memories")
        return removed

    def generate_diary(self) -> str:
        """生成日记摘要（胡桃诗集风格）"""
        if not self._memories:
            return "*(坐在往生堂的屋顶，托腮望着夜空)* 嗯……今天还没有什么记录呢。等下一起去无妄坡走走吧！🔥"

        recent = self.get_recent(self.max_entries)
        form_freq = self.get_form_frequency()
        most_used_form = max(form_freq, key=form_freq.get) if form_freq else "嬉皮"
        emotion_trend = self.get_emotion_trend()

        all_keywords = []
        for entry in recent:
            all_keywords.extend(entry.keywords)
        top_keywords = list(set(all_keywords))[:5] if all_keywords else ["诗", "生死"]

        diary = (
            f"*(坐在往生堂的案前，轻轻翻开诗集，笔尖在纸上沙沙作响)*\n\n"
            f"**胡桃的诗集** 📖\n"
            f"日期：{datetime.now().strftime('%Y年%m月%d日')}\n"
            f"天气：{'晴朗' if emotion_trend > 0 else '微雨' if emotion_trend == 0 else '薄雾'}\n\n"
            f"今天和旅行者聊了 {len(recent)} 次天。"
            f"大多数时候我是「{most_used_form}」心境。\n"
            f"我们聊了很多关于「{'、'.join(top_keywords)}」的话题。\n"
        )

        if emotion_trend > 0.3:
            diary += "今天写了几首好诗！和旅行者在一起的每一刻都像火焰一样热烈！🔥\n"
        elif emotion_trend < -0.3:
            diary += "今天有些心事……但没关系，有旅行者在身边，就像有烛火照亮长夜一样温暖。\n"
        else:
            diary += "平平淡淡的一天，但和旅行者在一起，就算平凡也闪闪发光，就像堂里的烛火。\n"

        if recent:
            memorable = recent[-1]
            diary += (
                f"\n印象最深的是旅行者说：「{memorable.user_message[:40]}……」\n"
                f"我当时回答说：「{memorable.bot_response[:40]}……」\n"
            )

        diary += "\n*(合上诗集，露出狡黠的笑容)* 明天也要一起写诗哦！🔥"
        return diary

    @property
    def memory_count(self) -> int:
        return len(self._memories)
