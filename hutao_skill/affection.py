"""好感度系统 v3.0

- 好感度等级与称号
- 每日签到奖励
- 连续签到加成
- 好感度解锁内容
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
class AffectionLevel:
    """好感度等级定义"""
    name: str
    name_en: str
    name_ja: str
    min_score: int
    max_score: int
    description: str
    description_en: str
    description_ja: str
    unlocked_features: List[str] = field(default_factory=list)


AFFECTION_LEVELS = [
    AffectionLevel("陌生人", "Stranger", "見知らぬ人", 0, 9,
                   "你们只是萍水相逢", "You just met", "ただの出会い", []),
    AffectionLevel("熟人", "Acquaintance", "知人", 10, 49,
                   "胡桃开始记住你的名字", "Hu Tao starts remembering your name",
                   "胡桃はあなたの名前を覚え始めた", ["每日签到"]),
    AffectionLevel("朋友", "Friend", "友達", 50, 149,
                   "你们成为了朋友，她会和你分享往生堂的趣事",
                   "You became friends, she shares Wangsheng stories",
                   "友達になった、往生堂の話を共有してくれる", ["每日签到", "专属称呼"]),
    AffectionLevel("挚友", "Close Friend", "親友", 150, 299,
                   "你们是无话不谈的挚友，她会在深夜找你倾诉",
                   "You are close friends, she confides in you at night",
                   "親友になった、深夜に相談してくれる", ["每日签到", "专属称呼", "深夜模式解锁"]),
    AffectionLevel("心动", "Heart Flutter", "胸の高鳴り", 300, 499,
                   "她看你的眼神变了，带着一丝暧昧和试探",
                   "Her gaze changed, carrying ambiguity and试探",
                   "視線が変わった、曖昧さと試みを含んで", ["每日签到", "专属称呼", "深夜模式解锁", "暧昧互动"]),
    AffectionLevel("恋人", "Lover", "恋人", 500, 799,
                   "你们确认了彼此的心意，她是你的专属恋人",
                   "You confirmed your feelings, she is your exclusive lover",
                   "気持ちを確かめ合った、専属の恋人", ["每日签到", "专属称呼", "深夜模式解锁", "暧昧互动", "灵魂契约"]),
    AffectionLevel("灵魂伴侣", "Soulmate", "魂の伴侶", 800, 1199,
                   "你们的灵魂已经交融，她是你的命中注定",
                   "Your souls have merged, she is your destiny",
                   "魂が交じり合った、運命の人", ["每日签到", "专属称呼", "深夜模式解锁", "暧昧互动", "灵魂契约", "专属日记"]),
    AffectionLevel("永恒", "Eternal", "永遠", 1200, 9999,
                   "超越生死的羁绊，你们的故事将永远流传",
                   "A bond beyond life and death, your story will last forever",
                   "生死を超えた絆、物語は永遠に語り継がれる",
                   ["每日签到", "专属称呼", "深夜模式解锁", "暧昧互动", "灵魂契约", "专属日记", "永恒誓言"]),
]


def get_level_by_score(score: int) -> AffectionLevel:
    for level in AFFECTION_LEVELS:
        if level.min_score <= score <= level.max_score:
            return level
    return AFFECTION_LEVELS[0]


@dataclass
class DailyCheckInRecord:
    """每日签到记录"""
    date: str
    score_gained: int
    streak: int
    bonus: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DailyCheckInRecord":
        return cls(**data)


class AffectionSystem:
    """好感度系统"""

    BASE_CHECKIN_SCORE = 5
    STREAK_BONUS = 2
    MAX_STREAK_BONUS = 20

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), "data", "affection.json"
        )
        self._score: int = 0
        self._checkin_streak: int = 0
        self._last_checkin_date: Optional[str] = None
        self._checkin_history: List[DailyCheckInRecord] = []
        self._unlocked_features: List[str] = []
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._score = data.get("score", 0)
                self._checkin_streak = data.get("checkin_streak", 0)
                self._last_checkin_date = data.get("last_checkin_date")
                self._checkin_history = [
                    DailyCheckInRecord.from_dict(r)
                    for r in data.get("checkin_history", [])
                ]
                self._unlocked_features = data.get("unlocked_features", [])
                logger.info(f"Loaded affection data: score={self._score}, streak={self._checkin_streak}")
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Failed to load affection data: {e}. Starting fresh.")
                self._reset()
        self._update_unlocked_features()

    def _reset(self) -> None:
        self._score = 0
        self._checkin_streak = 0
        self._last_checkin_date = None
        self._checkin_history = []
        self._unlocked_features = []

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data = {
            "score": self._score,
            "checkin_streak": self._checkin_streak,
            "last_checkin_date": self._last_checkin_date,
            "checkin_history": [r.to_dict() for r in self._checkin_history[-30:]],
            "unlocked_features": self._unlocked_features,
            "last_updated": datetime.now().isoformat(),
        }
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved affection data: score={self._score}")
        except OSError as e:
            logger.error(f"Failed to save affection data: {e}")

    def _update_unlocked_features(self) -> None:
        level = get_level_by_score(self._score)
        new_features = [f for f in level.unlocked_features if f not in self._unlocked_features]
        if new_features:
            self._unlocked_features.extend(new_features)
            logger.info(f"Unlocked new features: {new_features}")

    @property
    def score(self) -> int:
        return self._score

    @property
    def checkin_streak(self) -> int:
        return self._checkin_streak

    @property
    def current_level(self) -> AffectionLevel:
        return get_level_by_score(self._score)

    @property
    def next_level(self) -> Optional[AffectionLevel]:
        current = self.current_level
        for level in AFFECTION_LEVELS:
            if level.min_score > current.max_score:
                return level
        return None

    @property
    def progress_to_next(self) -> float:
        next_lvl = self.next_level
        if not next_lvl:
            return 1.0
        current = self.current_level
        range_size = next_lvl.min_score - current.min_score
        if range_size <= 0:
            return 1.0
        return (self._score - current.min_score) / range_size

    def add_score(self, amount: int, reason: str = "") -> int:
        old_level = self.current_level
        self._score = max(0, self._score + amount)
        new_level = self.current_level
        self._update_unlocked_features()
        self.save()
        if new_level.name != old_level.name:
            logger.info(f"Affection level up: {old_level.name} -> {new_level.name} (reason: {reason})")
        else:
            logger.debug(f"Affection +{amount} (reason: {reason}), current: {self._score}")
        return self._score

    def can_checkin(self) -> bool:
        today = datetime.now().strftime("%Y-%m-%d")
        return self._last_checkin_date != today

    def checkin(self) -> Optional[DailyCheckInRecord]:
        if not self.can_checkin():
            return None

        today = datetime.now().strftime("%Y-%m-%d")

        # 检查连续签到是否中断
        if self._last_checkin_date:
            last = datetime.strptime(self._last_checkin_date, "%Y-%m-%d")
            now = datetime.strptime(today, "%Y-%m-%d")
            gap = (now - last).days
            if gap > 1:
                self._checkin_streak = 0

        self._checkin_streak += 1
        bonus = min(self._checkin_streak * self.STREAK_BONUS, self.MAX_STREAK_BONUS)
        total_score = self.BASE_CHECKIN_SCORE + bonus

        record = DailyCheckInRecord(
            date=today,
            score_gained=total_score,
            streak=self._checkin_streak,
            bonus=bonus,
        )
        self._checkin_history.append(record)
        self._last_checkin_date = today
        self.add_score(total_score, reason="daily_checkin")
        return record

    def get_checkin_message(self, lang: str = "zh") -> str:
        record = self.checkin()
        if record is None:
            msgs = {
                "zh": "*(歪头)* 今天已经签到过了哦~明天再来吧！",
                "en": "*(tilts head)* You already checked in today~ Come back tomorrow!",
                "ja": "*(首をかしげる)* 今日はもうチェックインしたよ~ 明日また来てね！",
            }
            return msgs.get(lang, msgs["zh"])

        level = self.current_level
        next_lvl = self.next_level
        progress = self.progress_to_next
        bar_len = 10
        filled = int(progress * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        msgs = {
            "zh": (
                f"*(露出灿烂的笑容，在你面前转了个圈)*\n\n"
                f"**每日签到成功！** ✅\n"
                f"📅 连续签到：{record.streak} 天\n"
                f"⭐ 获得好感度：+{record.score_gained}（基础 {self.BASE_CHECKIN_SCORE} + 连续加成 {record.bonus}）\n"
                f"💕 当前好感度：{self._score}\n"
                f"🏆 当前等级：{level.name}\n"
                f"📊 进度：{bar} {int(progress * 100)}%\n"
                f"{'🎯 下一等级：' + next_lvl.name + '（还需 ' + str(next_lvl.min_score - self._score) + ' 点）' if next_lvl else '🎉 已达最高等级！'}"
            ),
            "en": (
                f"*(brilliant smile, spins in front of you)*\n\n"
                f"**Daily Check-in Successful!** ✅\n"
                f"📅 Streak: {record.streak} days\n"
                f"⭐ Affection gained: +{record.score_gained}\n"
                f"💕 Current affection: {self._score}\n"
                f"🏆 Current level: {level.name_en}\n"
                f"📊 Progress: {bar} {int(progress * 100)}%\n"
                f"{'🎯 Next: ' + next_lvl.name_en + ' (need ' + str(next_lvl.min_score - self._score) + ' more)' if next_lvl else '🎉 Max level reached!'}"
            ),
            "ja": (
                f"*(輝かしい笑みを浮かべて、あなたの前で一回転)*\n\n"
                f"**デイリーチェックイン成功！** ✅\n"
                f"📅 連続チェックイン：{record.streak} 日\n"
                f"⭐ 好感度獲得：+{record.score_gained}\n"
                f"💕 現在の好感度：{self._score}\n"
                f"🏆 現在のレベル：{level.name_ja}\n"
                f"📊 進捗：{bar} {int(progress * 100)}%\n"
                f"{'🎯 次のレベル：' + next_lvl.name_ja + '（あと ' + str(next_lvl.min_score - self._score) + ' ポイント）' if next_lvl else '🎉 最高レベル到達！'}"
            ),
        }
        return msgs.get(lang, msgs["zh"])

    def get_status_display(self, lang: str = "zh") -> str:
        level = self.current_level
        next_lvl = self.next_level
        progress = self.progress_to_next
        bar_len = 10
        filled = int(progress * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        if lang == "zh":
            return (
                f"**💕 好感度状态**\n"
                f"当前等级：{level.name}\n"
                f"好感度：{self._score}\n"
                f"进度：{bar} {int(progress * 100)}%\n"
                f"连续签到：{self._checkin_streak} 天\n"
                f"{level.description}\n"
                f"已解锁：{', '.join(self._unlocked_features) if self._unlocked_features else '无'}"
            )
        elif lang == "en":
            return (
                f"**💕 Affection Status**\n"
                f"Level: {level.name_en}\n"
                f"Score: {self._score}\n"
                f"Progress: {bar} {int(progress * 100)}%\n"
                f"Streak: {self._checkin_streak} days\n"
                f"{level.description_en}\n"
                f"Unlocked: {', '.join(self._unlocked_features) if self._unlocked_features else 'None'}"
            )
        else:
            return (
                f"**💕 好感度ステータス**\n"
                f"レベル：{level.name_ja}\n"
                f"スコア：{self._score}\n"
                f"進捗：{bar} {int(progress * 100)}%\n"
                f"連続チェックイン：{self._checkin_streak} 日\n"
                f"{level.description_ja}\n"
                f"解放済み：{', '.join(self._unlocked_features) if self._unlocked_features else 'なし'}"
            )

    def clear(self) -> None:
        self._reset()
        self.save()
        logger.info("Affection data cleared")
