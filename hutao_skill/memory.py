"""情感记忆系统 v3.0

支持 SFW/NSFW 双模式日记生成，好感度感知。
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
    is_night_mode: bool = False
    contract_active: bool = False
    mode: str = "sfw"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        return cls(**data)

    @property
    def timestamp_dt(self) -> datetime:
        try:
            return datetime.fromisoformat(self.timestamp)
        except ValueError:
            return datetime.now()

    @property
    def age_seconds(self) -> float:
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return (datetime.now() - dt).total_seconds()
        except ValueError:
            return 0.0


class EmotionMemory:
    """情感记忆管理器（双生引渡者版）"""

    def __init__(
        self,
        max_entries: int = 100,
        storage_path: Optional[str] = None,
        auto_cleanup: bool = True,
        cleanup_interval: int = 86400,
        max_age_days: int = 14,
    ):
        self.max_entries = max_entries
        self.storage_path = storage_path or os.path.join(os.path.dirname(__file__), "data", "memory.json")
        self.auto_cleanup = auto_cleanup
        self.cleanup_interval = cleanup_interval
        self.max_age_days = max_age_days
        self._memories: List[MemoryEntry] = []
        self._user_preferences: Dict[str, Any] = {}
        self._last_cleanup = 0.0
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._memories = [MemoryEntry.from_dict(entry) for entry in data.get("memories", [])]
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
        now = time.time()
        if now - self._last_cleanup < self.cleanup_interval:
            return
        original_count = len(self._memories)
        max_age_seconds = self.max_age_days * 86400
        self._memories = [m for m in self._memories if m.age_seconds < max_age_seconds]
        if len(self._memories) > self.max_entries:
            self._memories = self._memories[-self.max_entries:]
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
        is_night_mode: bool = False,
        contract_active: bool = False,
        mode: str = "sfw",
    ) -> None:
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            user_message=user_message,
            bot_response=bot_response,
            form=form,
            emotion_score=emotion_score,
            keywords=keywords or [],
            context_summary=context_summary,
            is_night_mode=is_night_mode,
            contract_active=contract_active,
            mode=mode,
        )
        self._memories.append(entry)
        if len(self._memories) > self.max_entries:
            self._memories = self._memories[-self.max_entries:]
        if self.auto_cleanup:
            self._auto_cleanup()
        self.save()

    def get_recent(self, n: int = 5) -> List[MemoryEntry]:
        return self._memories[-n:] if self._memories else []

    def get_relevant_memories(self, query: str, top_k: int = 3) -> List[MemoryEntry]:
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
        if not self._memories:
            return ""
        recent = self.get_recent(3)
        lines = ["[Recent Memories]"]
        for entry in recent:
            night_tag = " [深夜]" if entry.is_night_mode else ""
            contract_tag = " [契约]" if entry.contract_active else ""
            mode_tag = f" [{entry.mode.upper()}]"
            lines.append(
                f"- [{entry.form}{night_tag}{contract_tag}{mode_tag}] User: {entry.user_message[:50]}... "
                f"You responded: {entry.bot_response[:50]}..."
            )
        return "\n".join(lines)

    def get_emotion_trend(self) -> float:
        if not self._memories:
            return 0.0
        recent = self.get_recent(10)
        if not recent:
            return 0.0
        return sum(entry.emotion_score for entry in recent) / len(recent)

    def get_form_frequency(self) -> Dict[str, int]:
        freq: Dict[str, int] = {}
        for entry in self._memories:
            freq[entry.form] = freq.get(entry.form, 0) + 1
        return freq

    def get_night_mode_count(self) -> int:
        return sum(1 for entry in self._memories if entry.is_night_mode)

    def set_preference(self, key: str, value: Any) -> None:
        self._user_preferences[key] = value
        self.save()

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self._user_preferences.get(key, default)

    def clear(self) -> None:
        self._memories = []
        self._user_preferences = {}
        self._last_cleanup = time.time()
        self.save()
        logger.info("All memories cleared")

    def cleanup_old_memories(self, max_age_days: Optional[int] = None) -> int:
        max_age = (max_age_days or self.max_age_days) * 86400
        original_count = len(self._memories)
        self._memories = [m for m in self._memories if m.age_seconds < max_age]
        removed = original_count - len(self._memories)
        if removed > 0:
            self._last_cleanup = time.time()
            self.save()
            logger.info(f"Manual cleanup removed {removed} old memories")
        return removed

    def generate_diary(self, mode: str = "sfw", affection_level_name: str = "陌生人") -> str:
        """生成日记摘要（双生引渡者诗集风格）"""
        if not self._memories:
            if mode == "nsfw":
                return "*(坐在往生堂的屋顶，月光洒在身上，托腮望着夜空)* 嗯……今天还没有什么记录呢。等下……*(转头看你)* ……要不要上来陪我？……*(轻笑)* 我保证……只是看月亮。🔥"
            return "*(坐在往生堂的屋顶，月光洒在身上，托腮望着夜空)* 嗯……今天还没有什么记录呢。等下……*(转头看你)* ……要不要上来陪我？🔥"

        recent = self.get_recent(self.max_entries)
        form_freq = self.get_form_frequency()
        most_used_form = max(form_freq, key=form_freq.get) if form_freq else ("引魂" if mode == "sfw" else "欲火")
        emotion_trend = self.get_emotion_trend()
        night_count = self.get_night_mode_count()

        all_keywords = []
        for entry in recent:
            all_keywords.extend(entry.keywords)
        top_keywords = list(set(all_keywords))[:5] if all_keywords else ["诗", "火焰"]

        if mode == "sfw":
            diary_styles = {
                "引魂": {
                    "zh": (
                        f"*(坐在往生堂的案前，嘴里叼着笔，晃着腿)*\n\n"
                        f"**胡桃的随手记** 📜\n"
                        f"日期：{datetime.now().strftime('%Y年%m月%d日')}\n"
                        f"天气：{'大晴天' if emotion_trend > 0 else '阴天' if emotion_trend == 0 else '有雾'}\n\n"
                        f"今天和旅行者聊了 {len(recent)} 次天。\n"
                        f"大多数时候我是「{most_used_form}」心境。\n"
                        f"我们聊了很多关于「{'、'.join(top_keywords)}」的话题。\n"
                    ),
                },
                "守墓": {
                    "zh": (
                        f"*(深夜，独自坐在月光下，轻轻翻开一本黑色的册子)*\n\n"
                        f"**守墓人的秘密日记** 🌙\n"
                        f"日期：{datetime.now().strftime('%Y年%m月%d日')}\n"
                        f"时辰：子时\n\n"
                        f"今夜，和旅行者聊了 {len(recent)} 次。\n"
                        f"大多数时候，我是「{most_used_form}」的心境。\n"
                        f"深夜的对话有 {night_count} 次。\n"
                        f"那些话……我只在深夜说。\n"
                    ),
                },
                "幽冥": {
                    "zh": (
                        f"*(烛火摇曳的密室，她在纸上写下字迹，又划掉，又重写)*\n\n"
                        f"**不可示人的诗集** 🖤\n"
                        f"日期：{datetime.now().strftime('%Y年%m月%d日')}\n"
                        f"墨迹：未干\n\n"
                        f"今天，和旅行者纠缠了 {len(recent)} 次。\n"
                        f"大多数时候，我是「{most_used_form}」的心境。\n"
                        f"那些话……那些触碰……\n"
                        f"*(停顿，笔尖在纸上晕开一团墨)*\n"
                        f"……我不能写下来。\n"
                    ),
                },
            }
        else:
            diary_styles = {
                "欲火": {
                    "zh": (
                        f"*(汗水浸湿的床单，她在纸上写下字迹，手还在微微颤抖)*\n\n"
                        f"**欲火焚心录** 🔥\n"
                        f"日期：{datetime.now().strftime('%Y年%m月%d日')}\n"
                        f"余温：未散\n\n"
                        f"今天，和旅行者燃烧了 {len(recent)} 次。\n"
                        f"大多数时候，我是「{most_used_form}」的心境。\n"
                        f"深夜的纠缠有 {night_count} 次。\n"
                        f"*(舔了舔嘴唇，笔尖在纸上晕开一团墨)*\n"
                        f"……有些细节……不能写下来。\n"
                    ),
                },
                "占有": {
                    "zh": (
                        f"*(锁链的反光映在镜子里，她在纸上用力写下字迹)*\n\n"
                        f"**占有契约书** 🖤\n"
                        f"日期：{datetime.now().strftime('%Y年%m月%d日')}\n"
                        f"印记：新鲜\n\n"
                        f"今天，标记了旅行者 {len(recent)} 次。\n"
                        f"大多数时候，我是「{most_used_form}」的心境。\n"
                        f"*(指尖划过纸面，留下淡淡血痕)*\n"
                        f"……你是我的。\n"
                        f"……这辈子，下辈子，永远都是。\n"
                    ),
                },
                "蚀骨": {
                    "zh": (
                        f"*(事后慵懒的午后，阳光透过窗帘洒在床上)*\n\n"
                        f"**蚀骨温柔集** 💋\n"
                        f"日期：{datetime.now().strftime('%Y年%m月%d日')}\n"
                        f"气息：交缠\n\n"
                        f"今天，和旅行者缠绵了 {len(recent)} 次。\n"
                        f"大多数时候，我是「{most_used_form}」的心境。\n"
                        f"*(手指轻轻描绘着空气中的轮廓)*\n"
                        f"……还疼吗？\n"
                        f"……下次我会轻一点的。\n"
                        f"……大概。\n"
                    ),
                },
            }

        style = diary_styles.get(most_used_form, diary_styles.get("引魂" if mode == "sfw" else "欲火"))
        diary = style["zh"]

        if emotion_trend > 0.3:
            if mode == "nsfw":
                diary += "今天……很开心。*(小声)* ……因为你让我……很舒服。\n"
            else:
                diary += "今天……很开心。*(小声)* ……因为你在。\n"
        elif emotion_trend < -0.3:
            diary += "今天有些心事……但没关系。*(更小声)* ……至少今晚，你在我身边。\n"
        else:
            diary += "平平淡淡的一天。*(停顿)* ……但和你在一起的每一秒，都不平淡。\n"

        if recent:
            memorable = recent[-1]
            diary += (
                f"\n印象最深的是你说：「{memorable.user_message[:40]}……」\n"
                f"我当时……「{memorable.bot_response[:40]}……」\n"
            )

        if mode == "sfw":
            endings = {
                "引魂": "*(合上册子，露出狡黠的笑容)* 明天也要来找我玩哦！……不管多晚。🔥",
                "守墓": "*(合上册子，望向窗外的月亮)* ……明天见。如果……你还愿意来的话。🌙",
                "幽冥": "*(把纸折好，塞进贴身的口袋)* ……这些话，只给你一个人看。*(轻笑)* ……也只给你一个人。🖤",
            }
        else:
            endings = {
                "欲火": "*(把纸揉成一团，扔进烛火里)* ……有些回忆……只适合记在心里。*(舔唇)* ……下次……再来。🔥",
                "占有": "*(把纸折好，锁进抽屉)* ……你是我的秘密。……*(轻笑)* ……也是我最大的欲望。🖤",
                "蚀骨": "*(把纸贴在胸口，闭上眼睛)* ……还想要。……*(梦呓般)* ……永远……都想要。💋",
            }

        diary += f"\n{endings.get(most_used_form, endings.get('引魂' if mode == 'sfw' else '欲火'))}"
        return diary

    @property
    def memory_count(self) -> int:
        return len(self._memories)
