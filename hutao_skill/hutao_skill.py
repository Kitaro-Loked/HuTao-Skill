"""Hu Tao Soul Awakening Skill v1.0

胡桃·阴阳两界灵魂觉醒（统一角色心境状态系统）
功能：情感记忆系统、心境状态系统、多语言支持、动态心境切换、
      季节事件感知、互动小游戏（对诗/捉鬼/往生仪式）、日记功能、
      诗歌创作系统、JSON 配置化提示词

胡桃没有多个"形态"，而是根据对话内容自然切换"心境"：
- 嬉皮：鬼马精灵、爱开玩笑、黑色幽默
- 哲思：诗意深沉、生死达观、内省温柔
- 庄严：堂主职责、严肃认真、恪守规矩
"""

import json
import logging
import os
import random
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
    # Mock for testing
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


# 配置日志
logger = logging.getLogger(__name__)


def setup_logging(level: int = logging.INFO, structured: bool = False) -> None:
    """配置日志系统

    Args:
        level: 日志级别
        structured: 是否使用结构化日志（JSON格式）
    """
    if structured:
        fmt = '{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
    else:
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


class HuTaoSoulAwakening(BaseSkill):
    """胡桃阴阳两界 Skill 主类"""

    def __init__(self, config_path: Optional[str] = None):
        super().__init__()

        self._config_path = config_path or self._get_default_config_path()

        # 加载配置
        self._skill_config = self._load_skill_config()

        # 配置日志
        log_level = getattr(
            logging, self._skill_config.get("log_level", "INFO"), logging.INFO
        )
        structured_logging = self._skill_config.get("structured_logging", False)
        setup_logging(level=log_level, structured=structured_logging)

        self.name: str = self._skill_config.get("name", "HuTao_Soul_Awakening_Skill")
        self.description: str = self._skill_config.get(
            "description", "胡桃·阴阳两界灵魂觉醒"
        )
        self.version: str = self._skill_config.get("version", "1.0.0")
        self.language: str = self._skill_config.get("default_language", "zh")
        self.auto_shift_probability: float = self._skill_config.get(
            "auto_shift_probability", 0.15
        )
        self.emotion_keywords_enabled: bool = self._skill_config.get(
            "emotion_keywords_enabled", True
        )
        self.seasonal_events_enabled: bool = self._skill_config.get(
            "seasonal_events_enabled", True
        )
        self.proactive_chat_enabled: bool = self._skill_config.get(
            "proactive_chat_enabled", True
        )
        self.proactive_chat_interval: int = self._skill_config.get(
            "proactive_chat_interval", 8
        )

        # 当前心境状态
        self.current_emotion: str = "嬉皮"

        # 性能监控
        perf_config = self._skill_config.get("performance", {})
        slow_threshold = perf_config.get("slow_threshold", 1.0)
        self._perf_tracker = PerformanceTracker(
            enabled=perf_config.get("performance_tracking", True),
            slow_threshold=slow_threshold,
        )

        # 初始化子系统
        self._emotion_manager = EmotionManager(self._config_path)
        self._memory = EmotionMemory(
            max_entries=self._skill_config.get("memory_max_entries", 50),
            storage_path=os.path.join(
                os.path.dirname(__file__), "data", "memory.json"
            ),
            auto_cleanup=self._skill_config.get("memory_auto_cleanup", True),
            cleanup_interval=self._skill_config.get(
                "memory_cleanup_interval", 86400
            ),
            max_age_days=self._skill_config.get("memory_max_age_days", 7),
        )
        self._event_manager = SeasonalEventManager(self._config_path)
        self._minigame_manager = MinigameManager(self._config_path)

        # 对话计数器
        self._message_count: int = 0
        self._diary_interval: int = self._skill_config.get("diary_interval", 10)

        logger.info(
            f"HuTaoSoulAwakening v{self.version} initialized. "
            f"Language: {self.language}, Proactive chat: {self.proactive_chat_enabled}"
        )

    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        return os.path.join(os.path.dirname(__file__), "config.json")

    def _load_skill_config(self) -> Dict[str, Any]:
        """加载 Skill 配置"""
        if not os.path.exists(self._config_path):
            logger.error(f"Config file not found: {self._config_path}")
            raise FileNotFoundError(f"Config file not found: {self._config_path}")

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            skill_config = config.get("skill", {})
            # 合并 performance 和 monitoring 配置
            skill_config["performance"] = config.get("performance", {})
            skill_config["monitoring"] = config.get("monitoring", {})
            logger.debug("Skill config loaded successfully")
            return skill_config
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise

    # ============================================================
    # 辅助方法
    # ============================================================

    def _set_system_prompt(self, ctx: Any) -> None:
        """设置系统提示词（包含心境状态注入）"""
        base_prompt = get_system_prompt(self.language)

        # 注入心境状态追加内容
        emotion_addition = get_emotion_state_addition(self.current_emotion, self.language)
        if emotion_addition:
            prompt = f"{base_prompt}\n\n{emotion_addition}"
        else:
            prompt = base_prompt

        # 注入情感记忆
        memory_summary = self._memory.get_memory_summary()
        if memory_summary:
            prompt = f"{prompt}\n\n{memory_summary}"

        ctx.set_system_prompt(prompt)

    def _check_emotion_keywords(self, message: str) -> Optional[str]:
        """检查情感关键词并返回反射式回应"""
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
        """检查季节性事件"""
        if not self.seasonal_events_enabled:
            return None
        return self._event_manager.get_event_message(self.language)

    def _detect_emotion(self, message: str) -> Optional[str]:
        """检测心境状态"""
        return self._emotion_manager.detect_emotion(message)

    def _get_proactive_message(self) -> Optional[str]:
        """获取主动聊天消息"""
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
        """获取本地化文本"""
        texts = {
            "zh": {
                "current_emotion": "当前心境：{emotion}",
                "stats_title": "📊 胡桃属性",
                "memory_cleared": "*(歪头，露出狡黠的笑容)* 嗯……之前的记忆？被堂里的烛火照散啦！不过没关系，我们可以写新的诗、创造新的回忆！🔥",
                "diary_not_ready": "*(翻着诗集)* 唔……对话还不够多呢，再聊一会儿再写诗吧！",
                "language_changed": "语言已切换为：{lang}",
                "unknown_language": "不支持的语言：{lang}。支持：zh / en / ja",
                "game_list": "🎮 可用小游戏：\n",
                "unknown_game": "不知道这个游戏呢……可用游戏：\n",
                "proactive_on": "*(眼睛一亮)* 好呀好呀！那我会时不时来找你聊天的！",
                "proactive_off": "*(故作深沉)* 好吧……那我就不打扰你了。不过你要是寂寞了，可以叫我哦。",
                "help_text": (
                    "**胡桃·阴阳两界灵魂觉醒 v1.0** 🔥\n\n"
                    "📋 指令列表：\n"
                    "- `心境` - 查看当前心境状态\n"
                    "- `属性` - 查看胡桃角色属性\n"
                    "- `语言 <zh/en/ja>` - 切换语言\n"
                    "- `日记` - 查看对话总结（诗集风格）\n"
                    "- `清空记忆` - 清空情感记忆\n"
                    "- `小游戏 <游戏名>` - 玩互动小游戏\n"
                    "- `主动聊天 <开/关>` - 开启/关闭主动聊天\n"
                    "- `帮助` - 显示此帮助信息\n\n"
                    "🎭 心境：嬉皮 / 哲思 / 庄严\n"
                    "💫 对话中有 {prob}% 概率自然心境波动"
                ),
            },
            "en": {
                "current_emotion": "Current Mood: {emotion}",
                "stats_title": "📊 Hu Tao Stats",
                "memory_cleared": "*(tilts head with a mischievous smile)* Hmm... previous memories? They were scattered by the candlelight! But it's okay, we can write new poems and create new memories! 🔥",
                "diary_not_ready": "*(flipping through poetry book)* Mmm... not enough conversations yet, let's chat a bit more before writing poetry!",
                "language_changed": "Language changed to: {lang}",
                "unknown_language": "Unsupported language: {lang}. Supported: zh / en / ja",
                "game_list": "🎮 Available minigames:\n",
                "unknown_game": "I don't know that game... Available games:\n",
                "proactive_on": "*(eyes light up)* Great great! I'll come chat with you from time to time!",
                "proactive_off": "*(pretending to be solemn)* Alright... I won't bother you then. But if you get lonely, you can call me.",
                "help_text": (
                    "**Hu Tao: Soul Awakening v1.0** 🔥\n\n"
                    "📋 Command List:\n"
                    "- `mood` - View current mood\n"
                    "- `stats` - View character stats\n"
                    "- `language <zh/en/ja>` - Switch language\n"
                    "- `diary` - View conversation summary\n"
                    "- `clear memory` - Clear emotional memory\n"
                    "- `minigame <name>` - Play interactive minigames\n"
                    "- `proactive <on/off>` - Toggle proactive chat\n"
                    "- `help` - Show this help\n\n"
                    "🎭 Moods: Playful / Philosophical / Solemn\n"
                    "💫 {prob}% chance of mood fluctuation during conversation"
                ),
            },
            "ja": {
                "current_emotion": "現在の心境：{emotion}",
                "stats_title": "📊 胡桃ステータス",
                "memory_cleared": "*(首をかしげて、いたずらっぽく笑う)* うーん……前の記憶？堂の蝋燭の明かりに散らされちゃったみたい！でも大丈夫、新しい詩を書いて、新しい思い出を作ろう！🔥",
                "diary_not_ready": "*(詩集をめくる)* うーん……まだ会話が足りないね、もう少しおしゃべりしてから詩を書こう！",
                "language_changed": "言語を変更しました：{lang}",
                "unknown_language": "未対応の言語：{lang}。対応：zh / en / ja",
                "game_list": "🎮 利用可能なミニゲーム：\n",
                "unknown_game": "そのゲームは知らないな……利用可能なゲーム：\n",
                "proactive_on": "*(目を輝かせる)* やったやった！時々おしゃべりしに来るね！",
                "proactive_off": "*(わざと厳粛なふりをして)* わかった……じゃあ邪魔しないよ。でも寂しくなったら、呼んでね。",
                "help_text": (
                    "**胡桃·陰陽両界魂の覚醒 v1.0** 🔥\n\n"
                    "📋 コマンド一覧：\n"
                    "- `心境` - 現在の心境を確認\n"
                    "- `ステータス` - キャラクターステータスを確認\n"
                    "- `言語 <zh/en/ja>` - 言語を切り替え\n"
                    "- `日記` - 会話のまとめを見る\n"
                    "- `記憶消去` - 感情記憶を消去\n"
                    "- `ミニゲーム <名前>` - インタラクティブなミニゲームを遊ぶ\n"
                    "- `主动聊天 <オン/オフ>` - 主动チャットのオン/オフ\n"
                    "- `ヘルプ` - このヘルプを表示\n\n"
                    "🎭 心境：遊び心 / 哲学的 / 厳粛\n"
                    "💫 会話中に {prob}% の確率で自然な心境変動"
                ),
            },
        }
        lang_texts = texts.get(self.language, texts["zh"])
        text = lang_texts.get(key, key)
        return text.format(**kwargs)

    # ============================================================
    # 事件处理器
    # ============================================================

    @on_message()
    async def handle_message(self, ctx: Any) -> None:
        """处理普通消息：心境检测、情感关键词、季节事件、记忆记录、主动聊天"""
        user_id = getattr(ctx, "user_id", "anonymous")
        with self._perf_tracker.track("handle_message", user_id=user_id):
            try:
                message = getattr(ctx, "message", "")

                # 检查季节事件（首次对话时）
                if self._message_count == 0:
                    event_msg = self._check_seasonal_event()
                    if event_msg:
                        await ctx.send(event_msg)

                self._message_count += 1

                # 检测心境状态变化（基于内容）
                detected = self._detect_emotion(message)
                if detected and detected != self.current_emotion:
                    old_emotion = self.current_emotion
                    self.current_emotion = detected
                    logger.info(f"Emotion shift: {old_emotion} -> {detected}")

                    # 发送心境变化提示
                    shift_msgs = {
                        "zh": {
                            "嬉皮": "*(嘴角微微上扬，眼中闪过一丝狡黠)* 哎呀，说到这个我可就不困了！",
                            "哲思": "*(望向窗外，语气变得缓慢而深沉)* 嗯……这个话题，让我想到了一些事。",
                            "庄严": "*(收起折扇，神色一正)* 这件事……需要认真对待。",
                        },
                        "en": {
                            "嬉皮": "*(a sly glint in her eyes)* Oh, you really know how to pique my interest!",
                            "哲思": "*(gazing out the window, voice slowing)* Hmm... this reminds me of something.",
                            "庄严": "*(folding her fan, expression turning serious)* This matter... requires proper attention.",
                        },
                        "ja": {
                            "嬉皮": "*(口元が少し上がり、いたずらっぽい光が目に宿る)* あら、これは興味が湜いちゃうね！",
                            "哲思": "*(窓の外を見て、口調がゆっくりと深みを帯びる)* うーん……この話、何か思い出すな。",
                            "庄严": "*(扇子を畳んで、真剣な表情になる)* このことは……ちゃんと向き合わないとね。",
                        },
                    }
                    msg = shift_msgs.get(self.language, shift_msgs["zh"]).get(detected, "")
                    if msg:
                        await ctx.send(msg)

                # 自动随机心境波动
                elif random.random() < self.auto_shift_probability:
                    states = self._emotion_manager.get_all_states()
                    old_emotion = self.current_emotion
                    new_emotion = random.choice([s for s in states if s != old_emotion])
                    self.current_emotion = new_emotion
                    logger.info(f"Auto emotion shift: {old_emotion} -> {new_emotion}")

                # 检查情感关键词反射
                emotion_response = self._check_emotion_keywords(message)
                if emotion_response:
                    await ctx.send(emotion_response)

                # 主动聊天触发
                if (
                    self.proactive_chat_enabled
                    and self._message_count > 0
                    and self._message_count % self.proactive_chat_interval == 0
                ):
                    proactive_msg = self._get_proactive_message()
                    if proactive_msg:
                        await ctx.send(proactive_msg)

                # 设置系统提示词
                self._set_system_prompt(ctx)

                # 记录记忆上下文
                ctx._hutao_emotion = self.current_emotion
                ctx._hutao_memory = self._memory

                # 检查是否需要生成日记
                if self._message_count > 0 and self._message_count % self._diary_interval == 0:
                    diary = self._memory.generate_diary()
                    await ctx.send(f"\n\n*{diary}*")

            except Exception as e:
                logger.error(f"Error in handle_message: {e}", exc_info=True)
                await ctx.send("*(揉了揉眼睛)* 哎呀……刚才好像走神了，能再说一遍吗？")

    @on_command("心境")
    async def cmd_emotion(self, ctx: Any) -> None:
        """查看当前心境状态"""
        try:
            stats_display = self._emotion_manager.get_state_stats_display(
                self.current_emotion, self.language
            )
            await ctx.send(
                f"{self._get_localized_text('current_emotion', emotion=self.current_emotion)}\n"
                f"{stats_display}"
            )
        except Exception as e:
            logger.error(f"Error in cmd_emotion: {e}", exc_info=True)

    @on_command("属性")
    async def cmd_stats(self, ctx: Any) -> None:
        """查看胡桃角色属性"""
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            char = config.get("character", {})
            stats = char.get("stats", {})

            names = {
                "zh": ("胡桃", "往生堂七十七代堂主", "火"),
                "en": ("Hu Tao", "77th Director of Wangsheng Funeral Parlor", "Pyro"),
                "ja": ("胡桃", "往生堂七十七代目堂主", "炎"),
            }
            name, title, element = names.get(self.language, names["zh"])

            await ctx.send(
                f"{self._get_localized_text('stats_title')}\n"
                f"**{name}** ({title} · {element})\n"
                f"🛡️ 防御: {stats.get('defense', 65)} | ❤️ 生命: {stats.get('hp', 75)}\n"
                f"⚡ 速度: {stats.get('speed', 80)} | ⚔️ 攻击: {stats.get('attack', 85)}\n"
                f"🎯 暴击: {stats.get('crit_rate', 30)}%"
            )
        except Exception as e:
            logger.error(f"Error in cmd_stats: {e}", exc_info=True)

    @on_command("语言")
    async def cmd_language(self, ctx: Any) -> None:
        """切换语言"""
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
        """生成对话日记"""
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
        """清空情感记忆"""
        try:
            self._memory.clear()
            self._message_count = 0
            await ctx.send(self._get_localized_text("memory_cleared"))
        except Exception as e:
            logger.error(f"Error in cmd_clear_memory: {e}", exc_info=True)

    @on_command("小游戏")
    async def cmd_minigame(self, ctx: Any) -> None:
        """互动小游戏"""
        try:
            args = getattr(ctx, "get_args", lambda: "")()
            args = args.strip() if isinstance(args, str) else ""

            if not args:
                games = self._minigame_manager.list_games(self.language)
                await ctx.send(self._get_localized_text("game_list") + games)
                return

            if args in ["对诗", "poetry", "詩", "poem"]:
                await ctx.send(self._minigame_manager.play_poetry_game(self.language))
            elif args in ["捉鬼", "ghost", "幽霊", "ghost hunt"]:
                await ctx.send(self._minigame_manager.play_ghost_game(self.language))
            elif args in ["往生", "ritual", "儀式", "funeral"]:
                await ctx.send(self._minigame_manager.play_ritual_game(self.language))
            else:
                games = self._minigame_manager.list_games(self.language)
                await ctx.send(self._get_localized_text("unknown_game") + games)

        except Exception as e:
            logger.error(f"Error in cmd_minigame: {e}", exc_info=True)

    @on_command("主动聊天")
    async def cmd_proactive_chat(self, ctx: Any) -> None:
        """开启/关闭主动聊天"""
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
                await ctx.send(
                    f"当前主动聊天状态：{status}\n请输入：`主动聊天 开` 或 `主动聊天 关`"
                )

        except Exception as e:
            logger.error(f"Error in cmd_proactive_chat: {e}", exc_info=True)

    @on_command("帮助")
    async def cmd_help(self, ctx: Any) -> None:
        """显示帮助信息"""
        try:
            prob = int(self.auto_shift_probability * 100)
            proactive = "ON" if self.proactive_chat_enabled else "OFF"
            await ctx.send(
                self._get_localized_text("help_text", prob=prob, proactive=proactive)
            )
        except Exception as e:
            logger.error(f"Error in cmd_help: {e}", exc_info=True)

    @on_command("性能")
    async def cmd_performance(self, ctx: Any) -> None:
        """查看性能统计"""
        try:
            stats = self._perf_tracker.get_all_stats()
            if not stats:
                await ctx.send("*(歪头)* 还没有性能数据呢，再聊一会儿吧！")
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

    # ============================================================
    # 公共 API
    # ============================================================

    def record_interaction(
        self,
        user_message: str,
        bot_response: str,
        emotion_score: float = 0.0,
        keywords: Optional[List[str]] = None,
    ) -> None:
        """记录一次交互到情感记忆"""
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
        """获取记忆摘要"""
        return self._memory.get_memory_summary()

    def get_current_state_info(self) -> Dict[str, Any]:
        """获取当前状态信息"""
        state = self._emotion_manager.get_state(self.current_emotion)
        return {
            "emotion": self.current_emotion,
            "language": self.language,
            "emotion_tags": state.emotion_tags if state else [],
            "keywords": state.keywords if state else [],
            "proactive_chat": self.proactive_chat_enabled,
        }

    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取性能统计"""
        return self._perf_tracker.get_all_stats()
