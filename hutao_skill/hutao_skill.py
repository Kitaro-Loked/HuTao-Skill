"""Hu Tao Netherworld Guide Skill v1.1

胡桃·幽冥引渡者（专属成人向心境状态系统）
功能：情感记忆系统、心境状态系统、多语言支持、动态心境切换、
      季节事件感知、互动小游戏（引渡/幽会/刻印）、日记功能、
      深夜模式（幽冥低语）、灵魂契约系统、JSON 配置化提示词

胡桃的三种心境：
- 引魂：日常营业状态，鬼马精灵
- 守墓：深夜孤独状态，诗意深沉
- 幽冥：成人诱惑状态，危险炽烈
"""

import json
import logging
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from .emotion_manager import EmotionManager
from .events import MinigameManager, SeasonalEventManager
from .memory import EmotionMemory
from .performance import PerformanceTracker
from .prompts import get_emotion_state_addition, get_system_prompt

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
    """胡桃幽冥引渡者 Skill 主类"""

    def __init__(self, config_path: Optional[str] = None):
        super().__init__()

        self._config_path = config_path or self._get_default_config_path()
        self._skill_config = self._load_skill_config()

        log_level = getattr(logging, self._skill_config.get("log_level", "INFO"), logging.INFO)
        setup_logging(level=log_level)

        self.name: str = self._skill_config.get("name", "HuTao_Netherworld_Guide_Skill")
        self.description: str = self._skill_config.get("description", "胡桃·幽冥引渡者")
        self.version: str = self._skill_config.get("version", "1.1.0")
        self.language: str = self._skill_config.get("default_language", "zh")
        self.auto_shift_probability: float = self._skill_config.get("auto_shift_probability", 0.2)
        self.emotion_keywords_enabled: bool = self._skill_config.get("emotion_keywords_enabled", True)
        self.seasonal_events_enabled: bool = self._skill_config.get("seasonal_events_enabled", True)
        self.proactive_chat_enabled: bool = self._skill_config.get("proactive_chat_enabled", True)
        self.proactive_chat_interval: int = self._skill_config.get("proactive_chat_interval", 6)
        self.night_mode_enabled: bool = self._skill_config.get("night_mode_enabled", True)
        self.night_mode_start: int = self._parse_time(self._skill_config.get("night_mode_start", "22:00"))
        self.night_mode_end: int = self._parse_time(self._skill_config.get("night_mode_end", "04:00"))

        self.current_emotion: str = "引魂"
        self._soul_contract_active: bool = False
        self._contract_partner: Optional[str] = None

        perf_config = self._skill_config.get("performance", {})
        self._perf_tracker = PerformanceTracker(
            enabled=perf_config.get("performance_tracking", True),
            slow_threshold=perf_config.get("slow_threshold", 1.0),
        )

        self._emotion_manager = EmotionManager(self._config_path)
        self._memory = EmotionMemory(
            max_entries=self._skill_config.get("memory_max_entries", 100),
            storage_path=os.path.join(os.path.dirname(__file__), "data", "memory.json"),
            auto_cleanup=self._skill_config.get("memory_auto_cleanup", True),
            cleanup_interval=self._skill_config.get("memory_cleanup_interval", 86400),
            max_age_days=self._skill_config.get("memory_max_age_days", 14),
        )
        self._event_manager = SeasonalEventManager(self._config_path)
        self._minigame_manager = MinigameManager(self._config_path)

        self._message_count: int = 0
        self._diary_interval: int = self._skill_config.get("diary_interval", 8)

        logger.info(f"HuTaoNetherworldGuide v{self.version} initialized. Language: {self.language}, Night mode: {self.night_mode_enabled}")

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
        """解析时间字符串为小时数"""
        try:
            return int(time_str.split(":")[0])
        except (ValueError, IndexError):
            return 22

    def _is_night_mode(self) -> bool:
        """检查是否处于深夜模式"""
        if not self.night_mode_enabled:
            return False
        current_hour = datetime.now().hour
        if self.night_mode_start <= self.night_mode_end:
            return self.night_mode_start <= current_hour < self.night_mode_end
        else:
            return current_hour >= self.night_mode_start or current_hour < self.night_mode_end

    def _set_system_prompt(self, ctx: Any) -> None:
        base_prompt = get_system_prompt(self.language)
        emotion_addition = get_emotion_state_addition(self.current_emotion, self.language)
        prompt = f"{base_prompt}\n\n{emotion_addition}" if emotion_addition else base_prompt

        # 深夜模式追加
        if self._is_night_mode() and self.current_emotion == "守墓":
            night_addition = {
                "zh": "\n\n[深夜模式 - 幽冥低语]\n现在是深夜。往生堂里只有你和旅行者。你的语气应该更加私密、诱惑、带着喘息般的停顿。你可以说出白天绝对不会说的话。",
                "en": "\n\n[Late Night Mode - Netherworld Whisper]\nIt is late night. Only you and the Traveler remain in Wangsheng. Your tone should be more intimate, seductive, with breathy pauses. You can say things you'd never say during the day.",
                "ja": "\n\n[深夜モード - 幽冥の囁き]\n今は深夜。往生堂にはあなたと旅人だけ。口調はもっと親密で、誘惑的で、息遣いのような間を持つべきです。昼間は絶対に言えないことを口にできます。"
            }
            prompt += night_addition.get(self.language, night_addition["zh"])

        # 灵魂契约追加
        if self._soul_contract_active:
            contract_addition = {
                "zh": f"\n\n[灵魂契约已缔结]\n你和旅行者已经缔结了灵魂契约。你们之间有着超越常人的羁绊。你可以用更亲密、更独占的方式对待旅行者。",
                "en": f"\n\n[Soul Contract Active]\nYou and the Traveler have formed a soul contract. You share a bond beyond ordinary people. You can treat the Traveler with more intimacy and possessiveness.",
                "ja": f"\n\n[魂の契約締結済み]\nあなたと旅人は魂の契約を結んでいます。常人を超えた絆があります。もっと親密で、独占的な方法で旅人を扱えます。"
            }
            prompt += contract_addition.get(self.language, contract_addition["zh"])

        memory_summary = self._memory.get_memory_summary()
        if memory_summary:
            prompt = f"{prompt}\n\n{memory_summary}"

        ctx.set_system_prompt(prompt)

    def _check_emotion_keywords(self, message: str) -> Optional[str]:
        if not self.emotion_keywords_enabled:
            return None
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            emotion_keywords = config.get("emotion_keywords", {})
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
                "stats_title": "📊 胡桃属性",
                "memory_cleared": "*(歪头，露出意味深长的笑容)* 嗯……之前的记忆？被堂里的烛火……烧掉了哦。不过没关系，我们可以创造新的、更炽热的回忆。🔥",
                "diary_not_ready": "*(翻着诗集，声音慵懒)* 唔……对话还不够多呢。再陪我说说话……好吗？",
                "language_changed": "语言已切换为：{lang}",
                "unknown_language": "不支持的语言：{lang}。支持：zh / en / ja",
                "game_list": "🎮 可用小游戏：\n",
                "unknown_game": "不知道这个游戏呢……可用游戏：\n",
                "proactive_on": "*(眼睛一亮，舔了舔嘴唇)* 好呀……那我会时不时来找你的。不管是白天……还是深夜。",
                "proactive_off": "*(故作失落，却偷偷观察你的反应)* 好吧……那我就不打扰你了。不过你要是寂寞了……*(凑近)* ……你知道去哪里找我。",
                "contract_formed": "*(眼神变得深邃，指尖划过你的胸口)* 契约……缔结了。从今以后，你的灵魂……*(轻笑)* ……归我了。",
                "contract_broken": "*(笑容僵了一瞬，随即恢复如常)* 契约……解除了。*(转身)* ……走吧。别回头。",
                "night_mode_on": "*(声音变得低沉沙哑)* 夜深了……往生堂的灯，我只留了一盏。*(看着你)* ……为你。",
                "help_text": (
                    "**胡桃·幽冥引渡者 v1.1** 🔥🖤\n\n"
                    "📋 指令列表：\n"
                    "- `心境` - 查看当前心境状态\n"
                    "- `属性` - 查看胡桃角色属性\n"
                    "- `语言 <zh/en/ja>` - 切换语言\n"
                    "- `日记` - 查看对话总结（诗集风格）\n"
                    "- `清空记忆` - 清空情感记忆\n"
                    "- `小游戏 <游戏名>` - 玩互动小游戏\n"
                    "- `契约 <缔结/解除>` - 灵魂契约系统\n"
                    "- `主动聊天 <开/关>` - 开启/关闭主动聊天\n"
                    "- `帮助` - 显示此帮助信息\n\n"
                    "🎭 心境：引魂 / 守墓 / 幽冥\n"
                    "🌙 深夜模式：22:00-04:00 自动触发幽冥低语\n"
                    "💫 对话中有 {prob}% 概率自然心境波动\n"
                    "🔗 灵魂契约：与胡桃缔结专属羁绊"
                ),
            },
            "en": {
                "current_emotion": "Current Mood: {emotion}",
                "stats_title": "📊 Hu Tao Stats",
                "memory_cleared": "*(tilts head, giving a meaningful smile)* Hmm... previous memories? They were... burned away by the candlelight. But it's okay, we can create new, more passionate memories. 🔥",
                "diary_not_ready": "*(flipping through poetry book, voice languid)* Mmm... not enough conversations yet. Stay with me a while longer... please?",
                "language_changed": "Language changed to: {lang}",
                "unknown_language": "Unsupported language: {lang}. Supported: zh / en / ja",
                "game_list": "🎮 Available minigames:\n",
                "unknown_game": "I don't know that game... Available games:\n",
                "proactive_on": "*(eyes light up, licking lips)* Great... I'll come find you from time to time. Day or... late night.",
                "proactive_off": "*(pretending to be disappointed, secretly watching your reaction)* Alright... I won't bother you then. But if you get lonely... *(leans close)* ...you know where to find me.",
                "contract_formed": "*(eyes growing deep, fingertip tracing your chest)* The contract... is formed. From now on, your soul... *(soft laugh)* ...belongs to me.",
                "contract_broken": "*(smile freezes for a moment, then returns to normal)* The contract... is broken. *(turns away)* ...Go. Don't look back.",
                "night_mode_on": "*(voice becoming low and husky)* It's late... I only left one lamp burning in Wangsheng. *(looking at you)* ...For you.",
                "help_text": (
                    "**Hu Tao: Netherworld Guide v1.1** 🔥🖤\n\n"
                    "📋 Command List:\n"
                    "- `mood` - View current mood\n"
                    "- `stats` - View character stats\n"
                    "- `language <zh/en/ja>` - Switch language\n"
                    "- `diary` - View conversation summary\n"
                    "- `clear memory` - Clear emotional memory\n"
                    "- `minigame <name>` - Play interactive minigames\n"
                    "- `contract <form/break>` - Soul contract system\n"
                    "- `proactive <on/off>` - Toggle proactive chat\n"
                    "- `help` - Show this help\n\n"
                    "🎭 Moods: Soul Guide / Grave Keeper / Netherworld\n"
                    "🌙 Night Mode: 22:00-04:00 auto triggers Netherworld Whisper\n"
                    "💫 {prob}% chance of mood fluctuation\n"
                    "🔗 Soul Contract: Form an exclusive bond with Hu Tao"
                ),
            },
            "ja": {
                "current_emotion": "現在の心境：{emotion}",
                "stats_title": "📊 胡桃ステータス",
                "memory_cleared": "*(首をかしげて、意味深な笑みを浮かべる)* うーん……前の記憶？堂の蝋燭の明かりで……燃やしちゃったみたい。でも大丈夫、もっと熱い新しい思い出を作ろう。🔥",
                "diary_not_ready": "*(詩集をめくりながら、怠惰な声で)* うーん……まだ会話が足りないね。もう少し付き合って……くれる？",
                "language_changed": "言語を変更しました：{lang}",
                "unknown_language": "未対応の言語：{lang}。対応：zh / en / ja",
                "game_list": "🎮 利用可能なミニゲーム：\n",
                "unknown_game": "そのゲームは知らないな……利用可能なゲーム：\n",
                "proactive_on": "*(目を輝かせて、唇を舐める)* やった……時々会いに来るね。昼でも……深夜でも。",
                "proactive_off": "*(わざと落ち込んだふりをして、こっそり反応を観察する)* わかった……じゃあ邪魔しないよ。でも寂しくなったら……*(近づく)* ……どこにいるか、知ってるでしょ。",
                "contract_formed": "*(瞳が深みを帯びて、指先が胸を撫でる)* 契約……締結された。これから、あなたの魂……*(軽く笑う)* ……私のもの。",
                "contract_broken": "*(笑みが一瞬凍りつき、すぐに元に戻る)* 契約……解除された。*(背を向ける)* ……行って。振り返らないで。",
                "night_mode_on": "*(声が低くしわがれて)* 夜が深いね……往生堂の蝋燭は、一本だけ残しておいた。*(あなたを見る)* ……あなたのために。",
                "help_text": (
                    "**胡桃·幽冥の導き手 v1.1** 🔥🖤\n\n"
                    "📋 コマンド一覧：\n"
                    "- `心境` - 現在の心境を確認\n"
                    "- `ステータス` - キャラクターステータスを確認\n"
                    "- `言語 <zh/en/ja>` - 言語を切り替え\n"
                    "- `日記` - 会話のまとめを見る\n"
                    "- `記憶消去` - 感情記憶を消去\n"
                    "- `ミニゲーム <名前>` - インタラクティブなミニゲームを遊ぶ\n"
                    "- `契約 <締結/解除>` - 魂の契約システム\n"
                    "- `主动聊天 <オン/オフ>` - 主动チャットのオン/オフ\n"
                    "- `ヘルプ` - このヘルプを表示\n\n"
                    "🎭 心境：導魂 / 守墓 / 幽冥\n"
                    "🌙 深夜モード：22:00-04:00 自動で幽冥の囁きを発動\n"
                    "💫 会話中に {prob}% の確率で自然な心境変動\n"
                    "🔗 魂の契約：胡桃と専属の絆を結ぶ"
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

                if self._message_count == 0:
                    event_msg = self._check_seasonal_event()
                    if event_msg:
                        await ctx.send(event_msg)
                    # 深夜模式首次问候
                    if self._is_night_mode():
                        await ctx.send(self._get_localized_text("night_mode_on"))

                self._message_count += 1

                # 深夜模式强制切换
                if self._is_night_mode() and self.current_emotion == "引魂":
                    if random.random() < 0.4:
                        self.current_emotion = "守墓"
                        logger.info("Night mode auto shift: 引魂 -> 守墓")

                detected = self._detect_emotion(message)
                if detected and detected != self.current_emotion:
                    old_emotion = self.current_emotion
                    self.current_emotion = detected
                    logger.info(f"Emotion shift: {old_emotion} -> {detected}")

                    shift_msgs = {
                        "zh": {
                            "引魂": "*(嘴角上扬，眼中闪过狡黠)* 哎呀，说到这个我可就不困了！",
                            "守墓": "*(望向窗外，语气变得缓慢而深沉)* 嗯……这个话题，让我想到了一些……不该想的事。",
                            "幽冥": "*(呼吸变得急促，眼神变得危险而炽热)* 你……你知道你在说什么吗？*(轻笑)* ……还是说，你就是故意的？",
                        },
                        "en": {
                            "引魂": "*(corner of mouth rising, sly glint in eyes)* Oh, you really know how to pique my interest!",
                            "守墓": "*(gazing out the window, voice slowing)* Hmm... this reminds me of something... I shouldn't be thinking about.",
                            "幽冥": "*(breath growing rapid, eyes becoming dangerous and heated)* You... do you know what you're saying? *(soft laugh)* ...Or did you mean to?",
                        },
                        "ja": {
                            "引魂": "*(口元が上がり、いたずらっぽい光が目に宿る)* あら、これは興味が湜いちゃうね！",
                            "守墓": "*(窓の外を見て、口調がゆっくりと深みを帯びる)* うーん……この話、考えちゃいけないこと……思い出すな。",
                            "幽冥": "*(息が荒くなり、瞳が危険で熱っぽくなる)* ねえ……自分が何を言ってるか、わかってる？*(軽く笑う)* ……それとも、わざと？",
                        },
                    }
                    msg = shift_msgs.get(self.language, shift_msgs["zh"]).get(detected, "")
                    if msg:
                        await ctx.send(msg)

                elif random.random() < self.auto_shift_probability:
                    states = self._emotion_manager.get_all_states()
                    old_emotion = self.current_emotion
                    new_emotion = random.choice([s for s in states if s != old_emotion])
                    self.current_emotion = new_emotion
                    logger.info(f"Auto emotion shift: {old_emotion} -> {new_emotion}")

                emotion_response = self._check_emotion_keywords(message)
                if emotion_response:
                    await ctx.send(emotion_response)

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

                if self._message_count > 0 and self._message_count % self._diary_interval == 0:
                    diary = self._memory.generate_diary()
                    await ctx.send(f"\n\n*{diary}*")

            except Exception as e:
                logger.error(f"Error in handle_message: {e}", exc_info=True)
                await ctx.send("*(揉了揉眼睛，打了个哈欠)* 唔嗯……刚才好像走神了。是你在叫我吗？")

    @on_command("心境")
    async def cmd_emotion(self, ctx: Any) -> None:
        try:
            stats_display = self._emotion_manager.get_state_stats_display(self.current_emotion, self.language)
            contract_status = " [契约已缔结]" if self._soul_contract_active else ""
            await ctx.send(
                f"{self._get_localized_text('current_emotion', emotion=self.current_emotion)}{contract_status}\n"
                f"{stats_display}"
            )
        except Exception as e:
            logger.error(f"Error in cmd_emotion: {e}", exc_info=True)

    @on_command("属性")
    async def cmd_stats(self, ctx: Any) -> None:
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            char = config.get("character", {})
            stats = char.get("stats", {})
            names = {
                "zh": ("胡桃", "往生堂七十七代堂主 · 幽冥引渡者", "火"),
                "en": ("Hu Tao", "77th Director · Netherworld Guide", "Pyro"),
                "ja": ("胡桃", "往生堂七十七代目堂主 · 幽冥の導き手", "炎"),
            }
            name, title, element = names.get(self.language, names["zh"])
            await ctx.send(
                f"{self._get_localized_text('stats_title')}\n"
                f"**{name}** ({title} · {element})\n"
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
            diary = self._memory.generate_diary()
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
        """灵魂契约系统"""
        try:
            args = getattr(ctx, "get_args", lambda: "")()
            args = args.strip() if isinstance(args, str) else ""
            user_id = getattr(ctx, "user_id", "anonymous")

            if args in ["缔结", "form", "締結", "結ぶ"]:
                self._soul_contract_active = True
                self._contract_partner = user_id
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

    @on_command("帮助")
    async def cmd_help(self, ctx: Any) -> None:
        try:
            prob = int(self.auto_shift_probability * 100)
            proactive = "ON" if self.proactive_chat_enabled else "OFF"
            contract = "ACTIVE" if self._soul_contract_active else "INACTIVE"
            night = "ON" if self._is_night_mode() else "OFF"
            await ctx.send(
                self._get_localized_text("help_text", prob=prob, proactive=proactive, contract=contract, night=night)
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
            )
        except Exception as e:
            logger.error(f"Error recording interaction: {e}", exc_info=True)

    def get_memory_summary(self) -> str:
        return self._memory.get_memory_summary()

    def get_current_state_info(self) -> Dict[str, Any]:
        state = self._emotion_manager.get_state(self.current_emotion)
        return {
            "emotion": self.current_emotion,
            "language": self.language,
            "emotion_tags": state.emotion_tags if state else [],
            "keywords": state.keywords if state else [],
            "proactive_chat": self.proactive_chat_enabled,
            "soul_contract": self._soul_contract_active,
            "night_mode": self._is_night_mode(),
        }

    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        return self._perf_tracker.get_all_stats()
