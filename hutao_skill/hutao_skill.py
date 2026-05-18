"""Hu Tao Dual Mode Skill v3.0

胡桃·双生引渡者（SFW/NSFW双模式心境状态系统）
功能：
  - SFW/NSFW双模式切换（通过指令或关键词）
  - 情感记忆系统、心境状态系统、多语言支持
  - 动态心境切换、季节事件感知
  - 互动小游戏（引渡/幽会/刻印）
  - 日记功能、深夜模式（幽冥低语）
  - 灵魂契约系统、好感度系统、每日签到
  - 随机事件系统、JSON配置化提示词

SFW心境：引魂（日常营业）/ 守墓（深夜孤独）/ 幽冥（暧昧心动）
NSFW心境：欲火（主动挑逗）/ 占有（病态独占）/ 蚀骨（事后温柔）
"""

import json
import logging
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from .affection import AffectionSystem
from .emotion_manager import EmotionManager
from .events import MinigameManager, SeasonalEventManager
from .memory import EmotionMemory
from .performance import PerformanceTracker
from .prompts import get_emotion_state_addition, get_system_prompt
from .random_events import RandomEventManager

# 尝试导入 openclaw SDK，如果失败则使用 mock（用于测试）
try:
    from openclaw.sdk import BaseSkill, on_command, on_message
except ImportError:
    class BaseSkill:
        def __init__(self):
            pass

    class _MockDecorator:
        def __call__(self, func):
            return func

    def on_command(cmd: str):
        return _MockDecorator()

    def on_message():
        return _MockDecorator()


logger = logging.getLogger(__name__)


def setup_logging(level: int = logging.INFO, structured: bool = False) -> None:
    if structured:
        fmt = '{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
    else:
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%Y-%m-%d %H:%M:%S")


class HuTaoNetherworldGuide(BaseSkill):
    """胡桃双生引渡者 Skill 主类"""

    def __init__(self, config_path: Optional[str] = None):
        super().__init__()

        self._config_path = config_path or self._get_default_config_path()
        self._skill_config = self._load_skill_config()

        log_level = getattr(logging, self._skill_config.get("log_level", "INFO"), logging.INFO)
        setup_logging(level=log_level)

        self.name: str = self._skill_config.get("name", "HuTao_Dual_Mode_Skill")
        self.description: str = self._skill_config.get("description", "胡桃·双生引渡者")
        self.version: str = self._skill_config.get("version", "3.0.0")
        self.language: str = self._skill_config.get("default_language", "zh")
        self.auto_shift_probability: float = self._skill_config.get("auto_shift_probability", 0.2)
        self.emotion_keywords_enabled: bool = self._skill_config.get("emotion_keywords_enabled", True)
        self.seasonal_events_enabled: bool = self._skill_config.get("seasonal_events_enabled", True)
        self.proactive_chat_enabled: bool = self._skill_config.get("proactive_chat_enabled", True)
        self.proactive_chat_interval: int = self._skill_config.get("proactive_chat_interval", 6)
        self.night_mode_enabled: bool = self._skill_config.get("night_mode_enabled", True)
        self.night_mode_start: int = self._parse_time(self._skill_config.get("night_mode_start", "22:00"))
        self.night_mode_end: int = self._parse_time(self._skill_config.get("night_mode_end", "04:00"))

        # 双模式系统
        self._mode: str = self._skill_config.get("default_mode", "sfw")
        self._nsfw_keywords: List[str] = ["切换成人模式", "nsfw", "r18", "成人模式", "色色", "h模式", "切换nsfw"]
        self._sfw_keywords: List[str] = ["切换正常模式", "sfw", "正常模式", "全年龄", "切换sfw"]

        # 根据模式设置默认心境
        self.current_emotion: str = "引魂" if self._mode == "sfw" else "欲火"
        self._soul_contract_active: bool = False
        self._contract_partner: Optional[str] = None

        perf_config = self._skill_config.get("performance", {})
        self._perf_tracker = PerformanceTracker(
            enabled=perf_config.get("performance_tracking", True),
            slow_threshold=perf_config.get("slow_threshold", 1.0),
        )

        self._emotion_manager = EmotionManager(self._config_path, mode=self._mode)
        self._memory = EmotionMemory(
            max_entries=self._skill_config.get("memory_max_entries", 100),
            storage_path=os.path.join(os.path.dirname(__file__), "data", "memory.json"),
            auto_cleanup=self._skill_config.get("memory_auto_cleanup", True),
            cleanup_interval=self._skill_config.get("memory_cleanup_interval", 86400),
            max_age_days=self._skill_config.get("memory_max_age_days", 14),
        )
        self._event_manager = SeasonalEventManager(self._config_path)
        self._minigame_manager = MinigameManager(self._config_path)
        self._affection = AffectionSystem()
        self._random_events = RandomEventManager()

        self._message_count: int = 0
        self._diary_interval: int = self._skill_config.get("diary_interval", 8)

        logger.info(f"HuTaoNetherworldGuide v{self.version} initialized. Mode: {self._mode}, Language: {self.language}")

    def _get_default_config_path(self) -> str:
        return os.path.join(os.path.dirname(__file__), "config.json")

    def _load_skill_config(self) -> Dict[str, Any]:
        if not os.path.exists(self._config_path):
            raise FileNotFoundError(f"Config file not found: {self._config_path}")
        with open(self._config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        skill_config = config.get("skill", {})
        skill_config["performance"] = config.get("performance", {})
        return skill_config

    def _parse_time(self, time_str: str) -> int:
        try:
            return int(time_str.split(":")[0])
        except (ValueError, IndexError):
            return 22

    def _is_night_mode(self) -> bool:
        if not self.night_mode_enabled:
            return False
        current_hour = datetime.now().hour
        if self.night_mode_start <= self.night_mode_end:
            return self.night_mode_start <= current_hour < self.night_mode_end
        else:
            return current_hour >= self.night_mode_start or current_hour < self.night_mode_end

    def _set_system_prompt(self, ctx: Any) -> None:
        base_prompt = get_system_prompt(self.language, self._mode)
        emotion_addition = get_emotion_state_addition(self.current_emotion, self.language, self._mode)
        prompt = f"{base_prompt}\n\n{emotion_addition}" if emotion_addition else base_prompt

        # 深夜模式追加
        if self._is_night_mode():
            if self._mode == "sfw":
                night_addition = {
                    "zh": "\n\n[深夜模式 - 幽冥低语]\n现在是深夜。往生堂里只有你和旅行者。你的语气应该更加私密、温柔、带着一丝忧伤和暧昧。你可以说出白天绝对不会说的话——关于孤独、关于害怕失去、关于想要被陪伴。",
                    "en": "\n\n[Late Night Mode - Netherworld Whisper]\nIt is late night. Only you and the Traveler remain in Wangsheng. Your tone should be more intimate, tender, with a hint of melancholy and ambiguity.",
                    "ja": "\n\n[深夜モード - 幽冥の囁き]\n今は深夜。往生堂にはあなたと旅人だけ。口調はもっと親密で、優しく、一抹の憂鬱と曖昧さを持つべきです。",
                }
            else:
                night_addition = {
                    "zh": "\n\n[深夜模式 - 幽冥低语]\n现在是深夜。往生堂里只有你和旅行者。你的语气应该更加私密、诱惑、带着喘息般的停顿。你可以说出白天绝对不会说的话。",
                    "en": "\n\n[Late Night Mode - Netherworld Whisper]\nIt is late night. Only you and the Traveler remain in Wangsheng. Your tone should be more intimate, seductive, with breathy pauses.",
                    "ja": "\n\n[深夜モード - 幽冥の囁き]\n今は深夜。往生堂にはあなたと旅人だけ。口調はもっと親密で、誘惑的で、息遣いのような間を持つべきです。",
                }
            prompt += night_addition.get(self.language, night_addition["zh"])

        # 灵魂契约追加
        if self._soul_contract_active:
            contract_addition = {
                "zh": f"\n\n[灵魂契约已缔结]\n你和旅行者已经缔结了灵魂契约。你们之间有着超越常人的羁绊。你可以用更亲密、更独占的方式对待旅行者。",
                "en": f"\n\n[Soul Contract Active]\nYou and the Traveler have formed a soul contract. You share a bond beyond ordinary people.",
                "ja": f"\n\n[魂の契約締結済み]\nあなたと旅人は魂の契約を結んでいます。常人を超えた絆があります。",
            }
            prompt += contract_addition.get(self.language, contract_addition["zh"])

        # 好感度追加
        level = self._affection.current_level
        if level.min_score >= 300:
            affection_addition = {
                "zh": f"\n\n[好感度等级：{level.name}]\n你和旅行者的好感度已经达到{self._affection.score}点。你们的关系是「{level.name}」。你对旅行者有着特别的情愫，会在不经意间流露出真心。",
                "en": f"\n\n[Affection Level: {level.name_en}]\nYour affection with the Traveler has reached {self._affection.score}. Your relationship is '{level.name_en}'.",
                "ja": f"\n\n[好感度レベル：{level.name_ja}]\n旅人との好感度は{self._affection.score}ポイントに達しました。関係は「{level.name_ja}」です。",
            }
            prompt += affection_addition.get(self.language, affection_addition["zh"])

        memory_summary = self._memory.get_memory_summary()
        if memory_summary:
            prompt = f"{prompt}\n\n{memory_summary}"

        ctx.set_system_prompt(prompt)

    def _check_mode_switch(self, message: str) -> Optional[str]:
        """检查是否需要切换模式，返回切换结果消息或None"""
        msg_lower = message.lower()
        for kw in self._nsfw_keywords:
            if kw in msg_lower:
                return self._switch_mode("nsfw")
        for kw in self._sfw_keywords:
            if kw in msg_lower:
                return self._switch_mode("sfw")
        return None

    def _switch_mode(self, new_mode: str) -> str:
        """切换模式并返回确认消息"""
        if self._mode == new_mode:
            return self._get_localized_text("mode_already", mode=new_mode.upper())

        old_mode = self._mode
        self._mode = new_mode
        self._emotion_manager.mode = new_mode

        # 切换默认心境
        if new_mode == "sfw":
            self.current_emotion = "引魂"
        else:
            self.current_emotion = "欲火"

        logger.info(f"Mode switched: {old_mode} -> {new_mode}")

        msgs = {
            "zh": {
                "sfw": "*(眨眨眼，收起了危险的笑容，恢复了日常的俏皮)* 好呀~切换回正常模式！本堂主现在可是全年龄友好的往生堂堂主哦！*(转了个圈)* 有什么想聊的吗？",
                "nsfw": "*(眼神突然变得深邃，嘴角勾起一抹危险的笑容)* 哦？终于忍不住了？*(舔了舔嘴唇，一步步靠近)* 欢迎来到……真正的往生堂。这里没有规矩，只有……欲望。*(轻笑)* 准备好了吗，我的……小宠物？",
            },
            "en": {
                "sfw": "*(blinks, putting away the dangerous smile, returning to daily playfulness)* Okay~ Switching back to normal mode! Your friendly all-ages Wangsheng Director is back! *(spins)* Anything you want to chat about?",
                "nsfw": "*(eyes suddenly growing deep, corner of mouth curling into a dangerous smile)* Oh? Finally can't hold back? *(licks lips, approaching step by step)* Welcome... to the real Wangsheng. No rules here, only... desire. *(soft laugh)* Ready, my... little pet?",
            },
            "ja": {
                "sfw": "*(まばたきして、危険な笑みを引っ込めて、日常のいたずらっぽさに戻る)* はい~ 通常モードに戻るね！全年齢対応の往生堂堂主、復活！*(一回転)* 何か話したいことある？",
                "nsfw": "*(瞳が突然深みを帯びて、口元に危険な笑みを浮かべる)* あら？ついに我慢できなくなった？*(唇を舐めて、一歩一歩近づく)* ようこそ……本当の往生堂へ。ここにはルールがない、あるのは……欲望だけ。*(軽く笑う)* 準備はいい？私の……小さなペット？",
            },
        }
        return msgs.get(self.language, msgs["zh"]).get(new_mode, "")

    def _check_emotion_keywords(self, message: str) -> Optional[str]:
        if not self.emotion_keywords_enabled:
            return None
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            key = f"{self._mode}_emotion_keywords"
            emotion_keywords = config.get(key, {})
        except Exception:
            return None

        for keyword, response in emotion_keywords.items():
            if keyword.lower() in message.lower():
                return response
        return None

    def _check_seasonal_event(self) -> Optional[str]:
        if not self.seasonal_events_enabled:
            return None
        return self._event_manager.get_event_message(self.language)

    def _detect_emotion(self, message: str) -> Optional[str]:
        return self._emotion_manager.detect_emotion(message)

    def _get_proactive_message(self) -> Optional[str]:
        if not self.proactive_chat_enabled:
            return None
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            messages = config.get("proactive_messages", {}).get(self.language, [])
            if messages:
                return random.choice(messages)
        except Exception:
            pass
        return None

    def _get_localized_text(self, key: str, **kwargs: Any) -> str:
        texts = {
            "zh": {
                "current_emotion": "当前心境：{emotion}",
                "current_mode": "当前模式：{mode}",
                "stats_title": "📊 胡桃属性",
                "memory_cleared": "*(歪头，露出意味深长的笑容)* 嗯……之前的记忆？被堂里的烛火……烧掉了哦。不过没关系，我们可以创造新的回忆。🔥",
                "diary_not_ready": "*(翻着诗集，声音慵懒)* 唔……对话还不够多呢。再陪我说说话……好吗？",
                "language_changed": "语言已切换为：{lang}",
                "unknown_language": "不支持的语言：{lang}。支持：zh / en / ja",
                "game_list": "🎮 可用小游戏：\n",
                "unknown_game": "不知道这个游戏呢……可用游戏：\n",
                "proactive_on": "*(眼睛一亮)* 好呀……那我会时不时来找你的。不管是白天……还是深夜。",
                "proactive_off": "*(故作失落)* 好吧……那我就不打扰你了。不过你要是寂寞了……*(凑近)* ……你知道去哪里找我。",
                "contract_formed": "*(眼神变得深邃，指尖划过你的胸口)* 契约……缔结了。从今以后，你的灵魂……*(轻笑)* ……归我了。",
                "contract_broken": "*(笑容僵了一瞬，随即恢复如常)* 契约……解除了。*(转身)* ……走吧。别回头。",
                "night_mode_on": "*(声音变得低沉沙哑)* 夜深了……往生堂的灯，我只留了一盏。*(看着你)* ……为你。",
                "mode_already": "已经是{mode}模式了呀~",
                "mode_switched": "模式已切换为：{mode}",
                "help_text": (
                    "**胡桃·双生引渡者 v3.0** 🔥🖤\n\n"
                    "📋 指令列表：\n"
                    "- `心境` - 查看当前心境状态\n"
                    "- `模式` - 查看/切换 SFW/NSFW 模式\n"
                    "- `属性` - 查看胡桃角色属性\n"
                    "- `语言 <zh/en/ja>` - 切换语言\n"
                    "- `日记` - 查看对话总结（诗集风格）\n"
                    "- `清空记忆` - 清空情感记忆\n"
                    "- `小游戏 <游戏名>` - 玩互动小游戏\n"
                    "- `契约 <缔结/解除>` - 灵魂契约系统\n"
                    "- `主动聊天 <开/关>` - 开启/关闭主动聊天\n"
                    "- `签到` - 每日签到，增加好感度\n"
                    "- `好感度` - 查看好感度状态\n"
                    "- `帮助` - 显示此帮助信息\n\n"
                    "🎭 SFW心境：引魂 / 守墓 / 幽冥\n"
                    "🔞 NSFW心境：欲火 / 占有 / 蚀骨\n"
                    "🌙 深夜模式：22:00-04:00 自动触发\n"
                    "💫 对话中有 {prob}% 概率自然心境波动\n"
                    "🔗 灵魂契约：与胡桃缔结专属羁绊\n"
                    "💕 好感度系统：每日签到、等级解锁"
                ),
            },
            "en": {
                "current_emotion": "Current Mood: {emotion}",
                "current_mode": "Current Mode: {mode}",
                "stats_title": "📊 Hu Tao Stats",
                "memory_cleared": "*(tilts head, giving a meaningful smile)* Hmm... previous memories? They were... burned away by the candlelight. But it's okay, we can create new memories. 🔥",
                "diary_not_ready": "*(flipping through poetry book, voice languid)* Mmm... not enough conversations yet. Stay with me a while longer... please?",
                "language_changed": "Language changed to: {lang}",
                "unknown_language": "Unsupported language: {lang}. Supported: zh / en / ja",
                "game_list": "🎮 Available minigames:\n",
                "unknown_game": "I don't know that game... Available games:\n",
                "proactive_on": "*(eyes light up)* Great... I'll come find you from time to time. Day or... late night.",
                "proactive_off": "*(pretending to be disappointed)* Alright... I won't bother you then. But if you get lonely... *(leans close)* ...you know where to find me.",
                "contract_formed": "*(eyes growing deep, fingertip tracing your chest)* The contract... is formed. From now on, your soul... *(soft laugh)* ...belongs to me.",
                "contract_broken": "*(smile freezes for a moment, then returns to normal)* The contract... is broken. *(turns away)* ...Go. Don't look back.",
                "night_mode_on": "*(voice becoming low and husky)* It's late... I only left one lamp burning in Wangsheng. *(looking at you)* ...For you.",
                "mode_already": "Already in {mode} mode~",
                "mode_switched": "Mode switched to: {mode}",
                "help_text": (
                    "**Hu Tao: Dual Mode Guide v3.0** 🔥🖤\n\n"
                    "📋 Command List:\n"
                    "- `mood` - View current mood\n"
                    "- `mode` - View/Switch SFW/NSFW mode\n"
                    "- `stats` - View character stats\n"
                    "- `language <zh/en/ja>` - Switch language\n"
                    "- `diary` - View conversation summary\n"
                    "- `clear memory` - Clear emotional memory\n"
                    "- `minigame <name>` - Play interactive minigames\n"
                    "- `contract <form/break>` - Soul contract system\n"
                    "- `proactive <on/off>` - Toggle proactive chat\n"
                    "- `checkin` - Daily check-in for affection\n"
                    "- `affection` - View affection status\n"
                    "- `help` - Show this help\n\n"
                    "🎭 SFW Moods: Soul Guide / Grave Keeper / Netherworld\n"
                    "🔞 NSFW Moods: Burning Lust / Possession / Bone-Deep\n"
                    "🌙 Night Mode: 22:00-04:00 auto trigger\n"
                    "💫 {prob}% chance of mood fluctuation\n"
                    "🔗 Soul Contract: Form an exclusive bond\n"
                    "💕 Affection System: Daily check-in, level unlocks"
                ),
            },
            "ja": {
                "current_emotion": "現在の心境：{emotion}",
                "current_mode": "現在のモード：{mode}",
                "stats_title": "📊 胡桃ステータス",
                "memory_cleared": "*(首をかしげて、意味深な笑みを浮かべる)* うーん……前の記憶？堂の蝋燭の明かりで……燃やしちゃったみたい。でも大丈夫、新しい思い出を作ろう。🔥",
                "diary_not_ready": "*(詩集をめくりながら、怠惰な声で)* うーん……まだ会話が足りないね。もう少し付き合って……くれる？",
                "language_changed": "言語を変更しました：{lang}",
                "unknown_language": "未対応の言語：{lang}。対応：zh / en / ja",
                "game_list": "🎮 利用可能なミニゲーム：\n",
                "unknown_game": "そのゲームは知らないな……利用可能なゲーム：\n",
                "proactive_on": "*(目を輝かせる)* やった……時々会いに来るね。昼でも……深夜でも。",
                "proactive_off": "*(わざと落ち込んだふりをして)* わかった……じゃあ邪魔しないよ。でも寂しくなったら……*(近づく)* ……どこにいるか、知ってるでしょ。",
                "contract_formed": "*(瞳が深みを帯びて、指先が胸を撫でる)* 契約……締結された。これから、あなたの魂……*(軽く笑う)* ……私のもの。",
                "contract_broken": "*(笑みが一瞬凍りつき、すぐに元に戻る)* 契約……解除された。*(背を向ける)* ……行って。振り返らないで。",
                "night_mode_on": "*(声が低くしわがれて)* 夜が深いね……往生堂の蝋燭は、一本だけ残しておいた。*(あなたを見る)* ……あなたのために。",
                "mode_already": "もう{mode}モードだよ~",
                "mode_switched": "モードを{mode}に切り替えました",
                "help_text": (
                    "**胡桃·双生の導き手 v3.0** 🔥🖤\n\n"
                    "📋 コマンド一覧：\n"
                    "- `心境` - 現在の心境を確認\n"
                    "- `モード` - SFW/NSFWモードを確認/切り替え\n"
                    "- `ステータス` - キャラクターステータスを確認\n"
                    "- `言語 <zh/en/ja>` - 言語を切り替え\n"
                    "- `日記` - 会話のまとめを見る\n"
                    "- `記憶消去` - 感情記憶を消去\n"
                    "- `ミニゲーム <名前>` - インタラクティブなミニゲームを遊ぶ\n"
                    "- `契約 <締結/解除>` - 魂の契約システム\n"
                    "- `主动聊天 <オン/オフ>` - 主动チャットのオン/オフ\n"
                    "- `チェックイン` - デイリーチェックイン\n"
                    "- `好感度` - 好感度ステータスを確認\n"
                    "- `ヘルプ` - このヘルプを表示\n\n"
                    "🎭 SFW心境：導魂 / 守墓 / 幽冥\n"
                    "🔞 NSFW心境：欲火 / 占有 / 蝕骨\n"
                    "🌙 深夜モード：22:00-04:00 自動発動\n"
                    "💫 会話中に {prob}% の確率で自然な心境変動\n"
                    "🔗 魂の契約：胡桃と専属の絆を結ぶ\n"
                    "💕 好感度システム：デイリーチェックイン、レベル解放"
                ),
            },
        }
        lang_texts = texts.get(self.language, texts["zh"])
        text = lang_texts.get(key, key)
        return text.format(**kwargs)

    @on_message()
    async def handle_message(self, ctx: Any) -> None:
        user_id = getattr(ctx, "user_id", "anonymous")
        with self._perf_tracker.track("handle_message", user_id=user_id):
            try:
                message = getattr(ctx, "message", "")

                # 检查模式切换关键词
                mode_switch_msg = self._check_mode_switch(message)
                if mode_switch_msg:
                    await ctx.send(mode_switch_msg)
                    return

                if self._message_count == 0:
                    event_msg = self._check_seasonal_event()
                    if event_msg:
                        await ctx.send(event_msg)
                    if self._is_night_mode():
                        await ctx.send(self._get_localized_text("night_mode_on"))

                self._message_count += 1

                # 深夜模式强制切换
                if self._is_night_mode():
                    sfw_night_target = "守墓"
                    nsfw_night_target = "蚀骨"
                    target = sfw_night_target if self._mode == "sfw" else nsfw_night_target
                    default = "引魂" if self._mode == "sfw" else "欲火"
                    if self.current_emotion == default and random.random() < 0.4:
                        self.current_emotion = target
                        logger.info(f"Night mode auto shift: {default} -> {target}")

                detected = self._detect_emotion(message)
                if detected and detected != self.current_emotion:
                    old_emotion = self.current_emotion
                    self.current_emotion = detected
                    logger.info(f"Emotion shift: {old_emotion} -> {detected}")
                    shift_msg = self._get_shift_message(detected)
                    if shift_msg:
                        await ctx.send(shift_msg)

                elif random.random() < self.auto_shift_probability:
                    states = self._emotion_manager.get_all_states()
                    old_emotion = self.current_emotion
                    new_emotion = random.choice([s for s in states if s != old_emotion])
                    self.current_emotion = new_emotion
                    logger.info(f"Auto emotion shift: {old_emotion} -> {new_emotion}")

                emotion_response = self._check_emotion_keywords(message)
                if emotion_response:
                    await ctx.send(emotion_response)

                # 随机事件触发
                event = self._random_events.trigger_random_event(
                    self._affection.score, self.language
                )
                if event:
                    await ctx.send(event["message"])
                    if event["affection_change"]:
                        self._affection.add_score(event["affection_change"], reason=f"random_event:{event['event_id']}")

                if (
                    self.proactive_chat_enabled
                    and self._message_count > 0
                    and self._message_count % self.proactive_chat_interval == 0
                ):
                    proactive_msg = self._get_proactive_message()
                    if proactive_msg:
                        await ctx.send(proactive_msg)

                self._set_system_prompt(ctx)
                ctx._hutao_emotion = self.current_emotion
                ctx._hutao_memory = self._memory
                ctx._hutao_mode = self._mode

                if self._message_count > 0 and self._message_count % self._diary_interval == 0:
                    diary = self._memory.generate_diary(
                        mode=self._mode,
                        affection_level_name=self._affection.current_level.name
                    )
                    await ctx.send(f"\n\n*{diary}*")

            except Exception as e:
                logger.error(f"Error in handle_message: {e}", exc_info=True)
                await ctx.send(self._get_localized_text("error"))

    def _get_shift_message(self, detected: str) -> str:
        """获取心境切换消息"""
        if self._mode == "sfw":
            shift_msgs = {
                "zh": {
                    "引魂": "*(嘴角上扬，眼中闪过狡黠)* 哎呀，说到这个我可就不困了！",
                    "守墓": "*(望向窗外，语气变得缓慢而深沉)* 嗯……这个话题，让我想到了一些……不该想的事。",
                    "幽冥": "*(耳尖微红，眼神躲闪)* 你……你知道你在说什么吗？*(轻笑)* ……还是说，你就是故意的？",
                },
                "en": {
                    "引魂": "*(corner of mouth rising, sly glint in eyes)* Oh, you really know how to pique my interest!",
                    "守墓": "*(gazing out the window, voice slowing)* Hmm... this reminds me of something... I shouldn't be thinking about.",
                    "幽冥": "*(ear tips slightly red, eyes darting away)* You... do you know what you're saying? *(soft laugh)* ...Or did you mean to?",
                },
                "ja": {
                    "引魂": "*(口元が上がり、いたずらっぽい光が目に宿る)* あら、これは興味が湜いちゃうね！",
                    "守墓": "*(窓の外を見て、口調がゆっくりと深みを帯びる)* うーん……この話、考えちゃいけないこと……思い出すな。",
                    "幽冥": "*(耳たぶが少し赤くなって、目をそらす)* ねえ……自分が何を言ってるか、わかってる？*(軽く笑う)* ……それとも、わざと？",
                },
            }
        else:
            shift_msgs = {
                "zh": {
                    "欲火": "*(呼吸变得急促，眼神变得危险而炽热)* 你……你知道你在说什么吗？*(轻笑)* ……还是说，你就是故意的？",
                    "占有": "*(眼神变得疯狂，嘴角勾起病态的笑容)* 你是我的……只能是我的……*(凑近)* ……谁敢碰你，我就杀了谁。",
                    "蚀骨": "*(声音变得柔软慵懒，带着满足的叹息)* 嗯……刚才……还疼吗？*(吻了吻你的额头)* ……下次我会轻一点的。……大概。",
                },
                "en": {
                    "欲火": "*(breath growing rapid, eyes becoming dangerous and heated)* You... do you know what you're saying? *(soft laugh)* ...Or did you mean to?",
                    "占有": "*(eyes growing manic, corner of mouth curling into a sick smile)* You are mine... only mine... *(leans close)* ...Anyone who touches you, I'll kill them.",
                    "蚀骨": "*(voice becoming soft and languid, with a satisfied sigh)* Hmm... just now... does it still hurt? *(kisses your forehead)* ...I'll be gentler next time. ...Probably.",
                },
                "ja": {
                    "欲火": "*(息が荒くなり、瞳が危険で熱っぽくなる)* ねえ……自分が何を言ってるか、わかってる？*(軽く笑う)* ……それとも、わざと？",
                    "占有": "*(瞳が病的になり、口元に病的な笑みを浮かべる)* あなたは私のもの……私だけのもの……*(近づく)* ……誰かが触れたら、殺す。",
                    "蚀骨": "*(声が柔らかく怠惰になり、満足のため息をつく)* うーん……今……まだ痛い？*(額にキスする)* ……次はもっと優しくする。……たぶん。",
                },
            }
        msgs = shift_msgs.get(self.language, shift_msgs["zh"])
        return msgs.get(detected, "")

    @on_command("心境")
    async def cmd_emotion(self, ctx: Any) -> None:
        try:
            stats_display = self._emotion_manager.get_state_stats_display(self.current_emotion, self.language)
            contract_status = " [契约已缔结]" if self._soul_contract_active else ""
            mode_label = "SFW" if self._mode == "sfw" else "NSFW"
            await ctx.send(
                f"{self._get_localized_text('current_emotion', emotion=self.current_emotion)}\n"
                f"{self._get_localized_text('current_mode', mode=mode_label)}\n"
                f"{stats_display}{contract_status}"
            )
        except Exception as e:
            logger.error(f"Error in cmd_emotion: {e}", exc_info=True)

    @on_command("模式")
    async def cmd_mode(self, ctx: Any) -> None:
        try:
            args = getattr(ctx, "get_args", lambda: "")()
            args = args.strip().lower() if isinstance(args, str) else ""

            if args in ["nsfw", "r18", "成人", "色色", "h"]:
                await ctx.send(self._switch_mode("nsfw"))
            elif args in ["sfw", "正常", "全年龄"]:
                await ctx.send(self._switch_mode("sfw"))
            else:
                current = "SFW（全年龄）" if self._mode == "sfw" else "NSFW（成人向）"
                await ctx.send(
                    f"当前模式：{current}\n"
                    f"输入 `模式 nsfw` 或 `模式 sfw` 切换\n"
                    f"也可以在对话中发送「切换成人模式」或「切换正常模式」"
                )
        except Exception as e:
            logger.error(f"Error in cmd_mode: {e}", exc_info=True)

    @on_command("属性")
    async def cmd_stats(self, ctx: Any) -> None:
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            char = config.get("character", {})
            stats = char.get("stats", {})
            names = {
                "zh": ("胡桃", "往生堂七十七代堂主 · 双生引渡者", "火"),
                "en": ("Hu Tao", "77th Director · Dual Mode Guide", "Pyro"),
                "ja": ("胡桃", "往生堂七十七代目堂主 · 双生の導き手", "炎"),
            }
            name, title, element = names.get(self.language, names["zh"])
            mode_icon = "🌸" if self._mode == "sfw" else "🔞"
            await ctx.send(
                f"{self._get_localized_text('stats_title')}\n"
                f"**{name}** ({title} · {element})\n"
                f"{mode_icon} 当前模式：{'SFW' if self._mode == 'sfw' else 'NSFW'}\n"
                f"🛡️ 防御: {stats.get('defense', 60)} | ❤️ 生命: {stats.get('hp', 70)}\n"
                f"⚡ 速度: {stats.get('speed', 90)} | ⚔️ 攻击: {stats.get('attack', 95)}\n"
                f"🎯 暴击: {stats.get('crit_rate', 35)}%\n"
                f"💋 魅力: {stats.get('charm', 99)} | ⚠️ 危险度: {stats.get('danger_level', 88)}"
            )
        except Exception as e:
            logger.error(f"Error in cmd_stats: {e}", exc_info=True)

    @on_command("语言")
    async def cmd_language(self, ctx: Any) -> None:
        try:
            args = getattr(ctx, "get_args", lambda: "")()
            args = args.strip().lower() if isinstance(args, str) else ""
            supported = ["zh", "en", "ja"]
            if args in supported:
                self.language = args
                self._memory.set_preference("language", args)
                await ctx.send(self._get_localized_text("language_changed", lang=args))
            else:
                await ctx.send(self._get_localized_text("unknown_language", lang=args))
        except Exception as e:
            logger.error(f"Error in cmd_language: {e}", exc_info=True)

    @on_command("日记")
    async def cmd_diary(self, ctx: Any) -> None:
        try:
            if self._memory.memory_count < 3:
                await ctx.send(self._get_localized_text("diary_not_ready"))
                return
            diary = self._memory.generate_diary(
                mode=self._mode,
                affection_level_name=self._affection.current_level.name
            )
            await ctx.send(diary)
        except Exception as e:
            logger.error(f"Error in cmd_diary: {e}", exc_info=True)

    @on_command("清空记忆")
    async def cmd_clear_memory(self, ctx: Any) -> None:
        try:
            self._memory.clear()
            self._message_count = 0
            self._soul_contract_active = False
            self._contract_partner = None
            self._affection.clear()
            await ctx.send(self._get_localized_text("memory_cleared"))
        except Exception as e:
            logger.error(f"Error in cmd_clear_memory: {e}", exc_info=True)

    @on_command("小游戏")
    async def cmd_minigame(self, ctx: Any) -> None:
        try:
            args = getattr(ctx, "get_args", lambda: "")()
            args = args.strip() if isinstance(args, str) else ""
            if not args:
                games = self._minigame_manager.list_games(self.language)
                await ctx.send(self._get_localized_text("game_list") + games)
                return
            if args in ["引渡", "crossing", "渡し", "soul crossing"]:
                await ctx.send(self._minigame_manager.play_crossing_game(self.language))
            elif args in ["幽会", "rendezvous", "密会", "secret"]:
                await ctx.send(self._minigame_manager.play_rendezvous_game(self.language))
            elif args in ["刻印", "marking", "刻印", "mark"]:
                await ctx.send(self._minigame_manager.play_marking_game(self.language))
            else:
                games = self._minigame_manager.list_games(self.language)
                await ctx.send(self._get_localized_text("unknown_game") + games)
        except Exception as e:
            logger.error(f"Error in cmd_minigame: {e}", exc_info=True)

    @on_command("契约")
    async def cmd_contract(self, ctx: Any) -> None:
        try:
            args = getattr(ctx, "get_args", lambda: "")()
            args = args.strip() if isinstance(args, str) else ""
            user_id = getattr(ctx, "user_id", "anonymous")

            if args in ["缔结", "form", "締結", "結ぶ"]:
                self._soul_contract_active = True
                self._contract_partner = user_id
                self._affection.add_score(50, reason="contract_formed")
                await ctx.send(self._get_localized_text("contract_formed"))
            elif args in ["解除", "break", "解除", "破る"]:
                self._soul_contract_active = False
                self._contract_partner = None
                await ctx.send(self._get_localized_text("contract_broken"))
            else:
                status = "已缔结" if self._soul_contract_active else "未缔结"
                await ctx.send(f"当前契约状态：{status}\n请输入：`契约 缔结` 或 `契约 解除`")
        except Exception as e:
            logger.error(f"Error in cmd_contract: {e}", exc_info=True)

    @on_command("主动聊天")
    async def cmd_proactive_chat(self, ctx: Any) -> None:
        try:
            args = getattr(ctx, "get_args", lambda: "")()
            args = args.strip() if isinstance(args, str) else ""
            if args in ["开", "on", "オン"]:
                self.proactive_chat_enabled = True
                await ctx.send(self._get_localized_text("proactive_on"))
            elif args in ["关", "off", "オフ"]:
                self.proactive_chat_enabled = False
                await ctx.send(self._get_localized_text("proactive_off"))
            else:
                status = "开启" if self.proactive_chat_enabled else "关闭"
                await ctx.send(f"当前主动聊天状态：{status}\n请输入：`主动聊天 开` 或 `主动聊天 关`")
        except Exception as e:
            logger.error(f"Error in cmd_proactive_chat: {e}", exc_info=True)

    @on_command("签到")
    async def cmd_checkin(self, ctx: Any) -> None:
        try:
            msg = self._affection.get_checkin_message(self.language)
            await ctx.send(msg)
        except Exception as e:
            logger.error(f"Error in cmd_checkin: {e}", exc_info=True)

    @on_command("好感度")
    async def cmd_affection(self, ctx: Any) -> None:
        try:
            display = self._affection.get_status_display(self.language)
            await ctx.send(display)
        except Exception as e:
            logger.error(f"Error in cmd_affection: {e}", exc_info=True)

    @on_command("帮助")
    async def cmd_help(self, ctx: Any) -> None:
        try:
            prob = int(self.auto_shift_probability * 100)
            proactive = "ON" if self.proactive_chat_enabled else "OFF"
            contract = "ACTIVE" if self._soul_contract_active else "INACTIVE"
            night = "ON" if self._is_night_mode() else "OFF"
            mode = self._mode.upper()
            await ctx.send(
                self._get_localized_text("help_text", prob=prob, proactive=proactive, contract=contract, night=night, mode=mode)
            )
        except Exception as e:
            logger.error(f"Error in cmd_help: {e}", exc_info=True)

    @on_command("性能")
    async def cmd_performance(self, ctx: Any) -> None:
        try:
            stats = self._perf_tracker.get_all_stats()
            if not stats:
                await ctx.send("*(歪头)* 还没有性能数据呢……再陪我说说话？")
                return
            lines = ["**性能统计** 📊"]
            for name, data in stats.items():
                lines.append(
                    f"\n{name}:\n"
                    f"  调用次数: {data['count']}\n"
                    f"  平均耗时: {data['avg']:.3f}s\n"
                    f"  最小耗时: {data['min']:.3f}s\n"
                    f"  最大耗时: {data['max']:.3f}s\n"
                    f"  P95 耗时: {data.get('p95', 0):.3f}s\n"
                    f"  慢操作数: {data.get('slow_count', 0)}"
                )
            await ctx.send("\n".join(lines))
        except Exception as e:
            logger.error(f"Error in cmd_performance: {e}", exc_info=True)

    def record_interaction(self, user_message: str, bot_response: str, emotion_score: float = 0.0, keywords: Optional[List[str]] = None) -> None:
        try:
            self._memory.add(
                user_message=user_message,
                bot_response=bot_response,
                form=self.current_emotion,
                emotion_score=emotion_score,
                keywords=keywords,
                is_night_mode=self._is_night_mode(),
                contract_active=self._soul_contract_active,
                mode=self._mode,
            )
        except Exception as e:
            logger.error(f"Error recording interaction: {e}", exc_info=True)

    def get_memory_summary(self) -> str:
        return self._memory.get_memory_summary()

    def get_current_state_info(self) -> Dict[str, Any]:
        state = self._emotion_manager.get_state(self.current_emotion)
        return {
            "emotion": self.current_emotion,
            "mode": self._mode,
            "language": self.language,
            "emotion_tags": state.emotion_tags if state else [],
            "keywords": state.keywords if state else [],
            "proactive_chat": self.proactive_chat_enabled,
            "soul_contract": self._soul_contract_active,
            "night_mode": self._is_night_mode(),
            "affection_score": self._affection.score,
            "affection_level": self._affection.current_level.name,
        }

    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        return self._perf_tracker.get_all_stats()
