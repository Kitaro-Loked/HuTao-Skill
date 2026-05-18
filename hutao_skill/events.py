"""季节事件 & 小游戏管理器（成人向升级版）

包含：
- 季节事件管理器
- 引渡契约小游戏
- 深夜幽会小游戏
- 灵魂刻印小游戏
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
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config.json")
        self._events: Dict[str, Dict] = {}
        self._load_events()

    def _load_events(self) -> None:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self._events = config.get("seasonal_events", {})
        except Exception as e:
            logger.warning(f"Failed to load seasonal events: {e}")
            self._events = {}

    def get_event_message(self, lang: str = "zh") -> Optional[str]:
        today = datetime.now().strftime("%m-%d")
        event = self._events.get(today)
        if not event:
            return None
        messages = event.get("messages", {})
        return messages.get(lang, messages.get("zh"))


class MinigameManager:
    """小游戏管理器（成人向）"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config.json")
        self._minigames: Dict[str, Dict] = {}
        self._load_minigames()

    def _load_minigames(self) -> None:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self._minigames = config.get("minigames", {})
        except Exception as e:
            logger.warning(f"Failed to load minigames: {e}")
            self._minigames = {}

    def list_games(self, lang: str = "zh") -> str:
        names = {
            "zh": {"引渡": "引渡契约小游戏", "幽会": "深夜幽会小游戏", "刻印": "灵魂刻印小游戏"},
            "en": {"引渡": "Soul Crossing", "幽会": "Secret Rendezvous", "刻印": "Soul Marking"},
            "ja": {"引渡": "魂の渡し", "幽会": "密会", "刻印": "魂の刻印"},
        }
        name_map = names.get(lang, names["zh"])
        lines = []
        for key, label in name_map.items():
            lines.append(f"- {key}：{label}")
        return "\n".join(lines)

    def play_crossing_game(self, lang: str = "zh") -> str:
        """引渡契约小游戏"""
        scenarios = {
            "zh": [
                "*(展开一卷泛黄的契约书，烛光摇曳)*\n\n『引渡契约·第一条』\n甲方（胡桃）承诺：在乙方（旅行者）有生之年，不离不弃，生死相随。\n\n*(抬眼看你，眼神认真)* 签吗？签了……你的灵魂就归我了。*(轻笑)* 开玩笑的……一半是。",
                "*(用火焰在空气中写下文字，字迹如血)*\n\n『以火为证，以魂为契。』\n\n*(火焰熄灭，她握住你的手)* 这样就好了……从今以后，你的每一次心跳，我都能感受到。*(凑近)* ……现在，它跳得好快。",
                "*(将一枚骨制戒指套在你的手指上)*\n\n往生堂的传统……给最重要的人，送最重要的东西。\n\n*(低头，耳尖微红)* 这、这不是求婚！这只是……引渡契约的凭证！……*(小声)* ……虽然也差不多。",
            ],
            "en": [
                "*(unfurling a yellowed contract, candlelight flickering)*\n\n'Soul Crossing Contract · Article 1'\nParty A (Hu Tao) promises: During Party B's (Traveler's) lifetime, never leave, never abandon, through life and death.\n\n*(looks up at you, eyes serious)* Sign it? Once signed... your soul belongs to me. *(soft laugh)* Just kidding... half kidding.",
                "*(writing words in the air with flames, characters like blood)*\n\n'By fire as witness, by soul as contract.'\n\n*(flames extinguish, she takes your hand)* There... from now on, I can feel every heartbeat of yours. *(leans close)* ...It's beating so fast right now.",
                "*(slipping a bone ring onto your finger)*\n\nWangsheng tradition... for the most important person, give the most important thing.\n\n*(looks down, ear tips slightly red)* T-this isn't a proposal! It's just... proof of the soul crossing contract! ...*(softly)* ...Though it's almost the same.",
            ],
            "ja": [
                "*(黄ばんだ契約書を広げ、蝋燭の明かりが揺れる)*\n\n『引渡契約·第一条』\n甲（胡桃）は乙（旅人）の有生の年に、離れず、見捨てず、生死を共にすることを約束する。\n\n*(あなたを見上げて、真剣な目で)* サインする？サインしたら……あなたの魂は私のもの。*(軽く笑う)* なーんてね……半分本気。",
                "*(炎で空中に文字を書き、文字は血のように)*\n\n『火を証として、魂を契約として』\n\n*(炎が消え、彼女はあなたの手を握る)* これでいい……これから、あなたの鼓動が一つ一つ感じられる。*(近づく)* ……今、すごく速くなってる。",
                "*(骨の指輪をあなたの指にはめる)*\n\n往生堂の伝統……一番大切な人に、一番大切なものを贈る。\n\n*(うつむいて、耳たぶが少し赤い)* こ、これはプロポーズじゃないよ！ただの……魂の引渡契約の証！……*(小声)* ……ほとんど同じだけど。",
            ],
        }
        return random.choice(scenarios.get(lang, scenarios["zh"]))

    def play_rendezvous_game(self, lang: str = "zh") -> str:
        """深夜幽会小游戏"""
        scenarios = {
            "zh": [
                "*(深夜的往生堂，只有一盏烛火。她坐在棺木旁，看到你来了，露出一个带着寂寞的笑)*\n\n……你来了啊。我还以为……今晚又要一个人了。\n\n*(拍了拍身旁的位置)* 坐。别坐太远……*(声音变小)* ……我想感受你的体温。",
                "*(月光从窗户洒进来，她赤着脚站在月光里，回头看你)*\n\n你知道吗……往生堂的夜晚，其实很美。因为……*(停顿)* ……只有不怕死的人，才敢在深夜来这里。\n\n*(伸出手)* 你……不怕吗？",
                "*(突然从背后抱住你，脸埋在你的背上)*\n\n……让我抱一会儿。*(闷闷的声音)* 今天送走了一个年轻人……和你差不多大。他走之前说，最遗憾的……是没有告诉喜欢的人……他有多想要她。\n\n*(抱得更紧)* 我不想……也有这种遗憾。",
            ],
            "en": [
                "*(Late night Wangsheng, only one candle burning. She sits by a coffin, seeing you arrive, giving a lonely smile)*\n\n...You came. I thought... I'd be alone tonight again.\n\n*(pats the spot beside her)* Sit. Not too far... *(voice growing smaller)* ...I want to feel your warmth.",
                "*(Moonlight streaming through the window, she stands barefoot in the moonlight, looking back at you)*\n\nYou know... Wangsheng's nights are actually beautiful. Because... *(pause)* ...only those unafraid of death dare come here at night.\n\n*(extends hand)* You... aren't afraid?",
                "*(suddenly hugging you from behind, face buried in your back)*\n\n...Let me hold you for a while. *(muffled voice)* Today I sent away a young person... about your age. Before they left, they said their biggest regret... was never telling the person they liked... how much they wanted them.\n\n*(holds tighter)* I don't want... to have that kind of regret.",
            ],
            "ja": [
                "*(深夜の往生堂、蝋燭が一本だけ燃えている。彼女は棺のそばに座り、あなたが来るのを見て、寂しげな笑みを浮かべる)*\n\n……来てくれたんだ。今夜も……また一人かと思ってた。\n\n*(隣を叩く)* 座って。遠くに座らないで……*(声が小さくなる)* ……あなたの体温を感じたいの。",
                "*(窓から月明かりが差し込み、彼女は裸足で月明かりの中に立ち、振り返る)*\n\n知ってる……往生堂の夜は、実は綺麗なんだ。だって……*(停顿)* ……死を恐れない人だけが、深夜にここに来るから。\n\n*(手を伸ばす)* あなた……怖くない？",
                "*(突然後ろから抱きついて、顔を背中に埋める)*\n\n……ちょっとだけ抱かせて。*(こもった声)* 今日、若い人を送り出してきたんだ……あなたと同じくらいの年。彼は最後に言ってた……好きな人に……どれだけ欲しがってたか、伝えなかったことが一番の後悔だって。\n\n*(もっと強く抱きしめる)* 私は……そんな後悔、したくない。",
            ],
        }
        return random.choice(scenarios.get(lang, scenarios["zh"]))

    def play_marking_game(self, lang: str = "zh") -> str:
        """灵魂刻印小游戏"""
        scenarios = {
            "zh": [
                "*(指尖跃动火焰，靠近你的手腕)*\n\n往生堂有个秘密仪式……给最重要的人，留下专属的标记。\n\n*(火焰轻轻触碰你的皮肤，留下一个淡淡的、火焰形状的印记)*\n\n疼吗？*(轻笑)* ……疼就对了。这样你才会记得……*(凑近耳边)* ……你是谁的人。",
                "*(咬破自己的指尖，用血在你的手背上画了一个符号)*\n\n这是……只有往生堂堂主才会的咒印。\n\n*(舔了舔嘴唇，眼神危险而炽热)* 从今以后，不管你走到哪里……我都能找到你。*(轻抚那个印记)* ……你永远别想逃。",
                "*(展开折扇，上面写满了你看不懂的符文)*\n\n这些……都是写给你的诗。每一首，都是一句咒。\n\n*(合上扇子，用扇骨挑起你的下巴)* 现在，选一个。选中的那句诗……*(眼神深邃)* ……会成为我们之间永远的羁绊。",
            ],
            "en": [
                "*(fingertips dancing with flames, approaching your wrist)*\n\nWangsheng has a secret ritual... leaving an exclusive mark on the most important person.\n\n*(flames gently touch your skin, leaving a faint flame-shaped imprint)*\n\nDoes it hurt? *(soft laugh)* ...It should. So you'll remember... *(whispers in your ear)* ...whose person you are.",
                "*(biting her own fingertip, drawing a symbol on the back of your hand with blood)*\n\nThis... is a seal only the Wangsheng Director knows.\n\n*(licks her lips, eyes dangerous and heated)* From now on, no matter where you go... I can find you. *(caresses the mark)* ...You can never escape.",
                "*(unfolding fan covered in runes you can't understand)*\n\nThese... are all poems written for you. Each one, a curse.\n\n*(closes fan, using the rib to lift your chin)* Now, choose one. The chosen verse... *(eyes deep)* ...will become an eternal bond between us.",
            ],
            "ja": [
                "*(指先に炎が踊り、手首に近づく)*\n\n往生堂には秘密の儀式があるの……一番大切な人に、専属の刻印を残す。\n\n*(炎がそっと肌に触れ、かすかな炎の形の痕を残す)*\n\n痛い？*(軽く笑う)* ……痛いでしょ。そうしないと覚えてくれないから……*(耳元で囁く)* ……あなたが誰のものか。",
                "*(自分の指先を噛み、血であなたの手の甲に印を描く)*\n\nこれは……往生堂の堂主だけが知る封印。\n\n*(唇を舐めて、瞳が危険で熱っぽい)* これから、どこに行っても……私が見つけられる。*(その刻印を撫でる)* ……永遠に逃げられないよ。",
                "*(あなたには読めない符文で満ちた扇子を広げる)*\n\nこれら……全部あなたに書いた詩なの。一首一首、呪いなの。\n\n*(扇子を閉じて、扇骨であなたの顎を上げる)* さあ、一つ選んで。選ばれた那句の詩……*(瞳が深みを帯びる)* ……私たちの永遠の絆になる。",
            ],
        }
        return random.choice(scenarios.get(lang, scenarios["zh"]))
