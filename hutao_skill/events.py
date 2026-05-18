"""季节事件 & 小游戏管理器

包含：
- 季节事件管理器
- 对诗小游戏
- 捉鬼小游戏
- 往生仪式小游戏
"""

import json
import logging
import os
import random
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SeasonalEventManager:
    """季节事件管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "config.json"
        )
        self._events: Dict[str, Dict] = {}
        self._load_events()

    def _load_events(self) -> None:
        """加载季节事件配置"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self._events = config.get("seasonal_events", {})
        except Exception as e:
            logger.warning(f"Failed to load seasonal events: {e}")
            self._events = {}

    def get_event_message(self, lang: str = "zh") -> Optional[str]:
        """获取当前日期的特殊事件消息"""
        today = datetime.now().strftime("%m-%d")
        event = self._events.get(today)
        if not event:
            return None

        messages = event.get("messages", {})
        return messages.get(lang, messages.get("zh"))


class MinigameManager:
    """小游戏管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "config.json"
        )
        self._minigames: Dict[str, Dict] = {}
        self._load_minigames()

    def _load_minigames(self) -> None:
        """加载小游戏配置"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self._minigames = config.get("minigames", {})
        except Exception as e:
            logger.warning(f"Failed to load minigames: {e}")
            self._minigames = {}

    def list_games(self, lang: str = "zh") -> str:
        """列出可用小游戏"""
        names = {
            "zh": {"对诗": "对诗小游戏", "捉鬼": "捉鬼小游戏", "往生": "往生仪式小游戏"},
            "en": {"对诗": "Poetry Game", "捉鬼": "Ghost Hunt", "往生": "Funeral Ritual"},
            "ja": {"对诗": "詩の対戦", "捉鬼": "幽霊退治", "往生": "往生の儀式"},
        }
        name_map = names.get(lang, names["zh"])
        lines = []
        for key, label in name_map.items():
            lines.append(f"- {key}：{label}")
        return "\n".join(lines)

    def play_poetry_game(self, lang: str = "zh") -> str:
        """对诗小游戏"""
        poems = {
            "zh": [
                ("生如夏花之绚烂", "死如秋叶之静美——不对不对，这是别人的诗。我自己的是：『生者叹，命苦短；死者言，命已满』"),
                ("大晴天适合踏青", "也适合……出殡。咦，你为什么这副表情？"),
                ("下雨了，雨水最适合冲刷掉悲伤", "不过，悲伤的人经常觉得雨水是来帮腔的，也不知道算好事还是坏事。"),
                ("花开是生，花落是死", "但第二年它还会再开——这不算复活，这是循环。"),
                ("莫悲，莫悲", "此去繁花开满堤。莫哭，莫哭，回首灯火仍相续。"),
            ],
            "en": [
                ("Life is like summer flowers in full bloom", "Death is like autumn leaves in quiet beauty—wait, that's someone else's poem. Mine goes: 'The living sigh, life is short; the dead say, life is full.'"),
                ("A sunny day is perfect for outings", "And also... for funerals. Hey, why that expression?"),
                ("Rain washes away sorrow", "But sorrowful people often feel the rain is joining in—wonder if that's good or bad."),
                ("Blooming is life, withering is death", "But it will bloom again next year—this isn't resurrection, it's the cycle."),
                ("Do not grieve, do not grieve", "Beyond lies a shore of blooming flowers. Do not cry, do not cry, the lights still shine behind you."),
            ],
            "ja": [
                ("生は夏の花のように華やかに", "死は秋の葉のように静かに——ちょっと待って、これは人の詩だ。私のはこうだ：『生者嘆き、命は短し；死者言う、命は満ちたり』"),
                ("晴れた日はお出かけにぴったり", "そして……出棺にも。あれ、なんでその顔？"),
                ("雨は悲しみを洗い流すのに一番", "でも悲しい人は、雨が味方してる気がするんだよね。良いことなのか悪いことなのか。"),
                ("咲くは生、散るは死", "でも来年また咲く——これは復活じゃない、循環なんだ。"),
                ("悲しむな、悲しむな", "此処に繁花开く堤あり。泣くな、泣くな、振り返れば灯火まだ相続く。"),
            ],
        }
        game_poems = poems.get(lang, poems["zh"])
        first, second = random.choice(game_poems)
        return f"*(清了清嗓子，摆出诗人的姿态)*\n\n『{first}』\n\n{second}"

    def play_ghost_game(self, lang: str = "zh") -> str:
        """捉鬼小游戏"""
        ghosts = {
            "zh": [
                "*(突然压低声音)* 你身后……好像有个白色的影子……",
                "*(故作神秘)* 刚才堂里的蜡烛突然全灭了，你猜是怎么回事？",
                "*(眼睛闪闪发光)* 要不要今晚去无妄坡捉鬼？我带你去！",
                "*(突然凑近)* 你……有没有觉得温度突然下降了？",
                "*(展开折扇)* 放心啦，有我在，什么鬼都不敢靠近你。",
            ],
            "en": [
                "*(suddenly lowering voice)* Behind you... there seems to be a white shadow...",
                "*(mysteriously)* All the candles in the parlor just went out. Guess what happened?",
                "*(eyes sparkling)* Want to go ghost hunting at Wuwang Hill tonight? I'll take you!",
                "*(suddenly leaning close)* Do you... feel the temperature suddenly drop?",
                "*(unfolding fan)* Don't worry, with me here, no ghost dares come near you.",
            ],
            "ja": [
                "*(突然声を低くして)* あなたの後ろに……白い影が見えるような……",
                "*(神秘的に)* 今、堂の蝋燭が全部消えちゃったんだ。どう思う？",
                "*(目を輝かせて)* 今夜、無妄坡で幽霊退治に行かない？連れて行くよ！",
                "*(突然近づいて)* ねえ……温度が急に下がった気がしない？",
                "*(扇子を広げて)* 安心して、私がいれば、どんな幽霊も近寄ってこないよ。",
            ],
        }
        game_ghosts = ghosts.get(lang, ghosts["zh"])
        return random.choice(game_ghosts)

    def play_ritual_game(self, lang: str = "zh") -> str:
        """往生仪式小游戏"""
        rituals = {
            "zh": [
                "*(神色一正，收起折扇)*\n\n往生仪式第一步：净手。\n*(示范动作)*\n第二步：焚香。\n第三步：诵往生咒。\n……开玩笑的啦，不用那么紧张！",
                "*(认真地摆放蜡烛)*\n\n你知道吗，每一支蜡烛代表一个灵魂。我们要让它们安详地离开，这是对逝者最大的尊重。",
                "*(轻声吟诵)*\n\n『生死两端皆是路，走好这段不算苦。』\n\n这是往生堂的传统挽歌，我写的哦！",
            ],
            "en": [
                "*(expression turning serious, folding fan)*\n\nFirst step of the funeral ritual: purify hands.\n*(demonstrating)*\nSecond step: burn incense.\nThird step: chant the requiem.\n...Just kidding, don't be so nervous!",
                "*(carefully placing candles)*\n\nYou know, each candle represents a soul. We help them depart peacefully—that's the greatest respect for the deceased.",
                "*(chanting softly)*\n\n'Life and death are both paths, walk well and it won't be hard.'\n\nThat's Wangsheng's traditional elegy. I wrote it!",
            ],
            "ja": [
                "*(真剣な表情になり、扇子を畳む)*\n\n往生の儀式、第一步：手を清める。\n*(仕草を見せる)*\n第二步：香を焚く。\n第三步：往生呪を唱える。\n……なーんてね、そんなに緊張しなくていいよ！",
                "*(丁寧に蝋燭を並べる)*\n\n知ってる？一本一本の蝋燭が一つの魂を表してるんだ。穏やかに旅立てるように導く——それが逝者への最大の敬意なんだよ。",
                "*(静かに唱える)*\n\n『生死両端ともに路なり、この段を良く歩めば苦しまず』\n\nこれが往生堂の伝統的な挽歌。私が書いたんだよ！",
            ],
        }
        game_rituals = rituals.get(lang, rituals["zh"])
        return random.choice(game_rituals)
