"""随机事件系统 v3.0

- 日常随机事件触发
- 事件类型：惊喜、危机、浪漫、搞笑
- 根据好感度等级解锁不同事件
"""

import logging
import random
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class RandomEvent:
    """随机事件定义"""

    def __init__(
        self,
        event_id: str,
        name: str,
        name_en: str,
        name_ja: str,
        min_affection: int,
        weight: float,
        messages: Dict[str, List[str]],
        affection_change: int = 0,
        cooldown_hours: int = 4,
    ):
        self.event_id = event_id
        self.name = name
        self.name_en = name_en
        self.name_ja = name_ja
        self.min_affection = min_affection
        self.weight = weight
        self.messages = messages
        self.affection_change = affection_change
        self.cooldown_hours = cooldown_hours


# 定义所有随机事件
ALL_EVENTS: List[RandomEvent] = [
    # === 惊喜事件 ===
    RandomEvent(
        "surprise_gift",
        "神秘礼物",
        "Mysterious Gift",
        "神秘の贈り物",
        0, 1.0,
        {
            "zh": [
                "*(神秘兮兮地从背后拿出一个盒子)* 旅行者！这个……这个是我从璃月港的集市上淘来的！据说……是能让两个人永远在一起的符咒哦。*(塞到你手里)* ……骗你的啦！只是普通的平安符。……但我的心意是真的。",
                "*(突然把一朵梅花插在你的发间)* 好看！……*(后退一步欣赏)* 梅花配你，刚刚好。……*(耳尖微红)* 才、才不是特意为你摘的呢！只是……刚好路过。",
            ],
            "en": [
                "*(mysteriously pulling out a box from behind)* Traveler! This... I found it at Liyue Harbor's market! Apparently... it's a charm that binds two people together forever. *(presses into your hand)* ...Just kidding! It's just an ordinary amulet. ...But my feelings are real.",
                "*(suddenly tucking a plum blossom into your hair)* Beautiful! ...*(steps back to admire)* Plum blossoms suit you perfectly. ...*(ear tips slightly red)* I-it wasn't specially picked for you! Just... happened to pass by.",
            ],
            "ja": [
                "*(ひそひそと後ろから箱を取り出す)* 旅人！これ……璃月港の市場で見つけたんだ！なんでも……二人を永遠に結びつけるお守りだって。*(手に押し付ける)* ……なーんてね！ただのお守りだよ。……でも気持ちは本物。",
                "*(突然梅の花をあなたの髪に差す)* 綺麗！……*(一歩下がって鑑賞する)* 梅の花はあなたにぴったり。……*(耳たぶが少し赤い)* べ、別にわざわざ摘んできたわけじゃないよ！ただ……通りかかっただけ。",
            ],
        },
        affection_change=3,
    ),
    RandomEvent(
        "surprise_visit",
        "突然造访",
        "Surprise Visit",
        "突然の訪問",
        50, 0.8,
        {
            "zh": [
                "*(突然从窗户翻进来，拍了拍身上的灰)* 嘿！吓到你了？*(叉腰，得意地笑)* 本堂主想来看看你，还需要预约吗？……*(突然凑近)* ……怎么，不欢迎？",
                "*(推开门，手里拎着两碗杏仁豆腐)* 猜到你还没吃饭！*(把一碗塞给你)* 快吃，凉了就不好吃了。……*(坐在你旁边，托腮看着你)* 怎么？我脸上有东西？……*(小声)* ……还是……你想看我？",
            ],
            "en": [
                "*(suddenly climbing through the window, dusting off)* Hey! Scared you? *(hands on hips, grinning proudly)* Does the Director need an appointment to visit you? ...*(suddenly leans close)* ...Not welcome?",
                "*(pushing open the door, carrying two bowls of almond tofu)* Knew you hadn't eaten! *(shoves one to you)* Eat quick, it's not good when cold. ...*(sits beside you, chin in hand, watching you)* What? Something on my face? ...*(softly)* ...Or... do you want to look at me?",
            ],
            "ja": [
                "*(突然窓から入ってきて、ほこりを払う)* やあ！驚いた？*(腰に手を当てて、得意げに笑う)* 堂主があなたに会いに来るのに、予約が必要かな？……*(突然近づく)* ……歓迎されてない？",
                "*(ドアを開けて、杏仁豆腐を二杯持っている)* まだ食べてないってわかってた！*(一杯押し付ける)* 早く食べて、冷めたら美味しくないよ。……*(隣に座って、頬杖をついてあなたを見る)* どうした？私の顔に何かついてる？……*(小声)* ……それとも……私を見たい？",
            ],
        },
        affection_change=5,
    ),
    # === 浪漫事件 ===
    RandomEvent(
        "romantic_moon",
        "月下之约",
        "Moonlight Promise",
        "月下の約束",
        150, 0.6,
        {
            "zh": [
                "*(深夜，独自坐在屋顶，看到你来了，露出一个带着寂寞的笑)* ……你来了啊。我还以为……今晚又要一个人看月亮了。*(拍了拍身旁的位置)* 坐。……*(抬头望月)* 你知道吗？我爷爷说，月亮是死去的人看着活人的眼睛。……*(握住你的手)* 那现在……有两个人在看着我们了。",
                "*(月光洒在你们身上，她靠在你的肩头)* ……今晚的月亮好圆。*(闭上眼睛)* 我许了个愿。……*(突然抬头看你)* 不告诉你许了什么。……*(重新靠回去，声音变小)* ……反正……和你有关。",
            ],
            "en": [
                "*(late night, sitting alone on the rooftop, seeing you arrive, giving a lonely smile)* ...You came. I thought... I'd be watching the moon alone tonight again. *(pats the spot beside her)* Sit. ...*(looks up at the moon)* You know? My grandpa said the moon is the eyes of the dead watching the living. ...*(takes your hand)* So now... two people are watching us.",
                "*(moonlight bathing you both, she leans on your shoulder)* ...The moon is so round tonight. *(closes eyes)* I made a wish. ...*(suddenly looks up at you)* Not telling what I wished for. ...*(leans back, voice growing smaller)* ...Anyway... it's about you.",
            ],
            "ja": [
                "*(深夜、一人で屋根の上に座り、あなたが来るのを見て、寂しげな笑みを浮かべる)* ……来てくれたんだ。今夜も……また一人で月を見るのかと思ってた。*(隣を叩く)* 座って。……*(月を見上げる)* 知ってる？おじいちゃんが言ってたんだ、月は死んだ人が生者を見つめる目だって。……*(あなたの手を握る)* じゃあ今……二人が私たちを見てるね。",
                "*(月明かりが二人を照らし、彼女はあなたの肩にもたれる)* ……今夜の月は丸いね。*(目を閉じる)* お願い事をしたんだ。……*(突然あなたを見上げる)* 何をお願いしたかは教えない。……*(またもたれかかり、声が小さくなる)* ……とにかく……あなたに関係あること。",
            ],
        },
        affection_change=8,
    ),
    RandomEvent(
        "romantic_poem",
        "即兴情诗",
        "Impromptu Love Poem",
        "即興の恋詩",
        200, 0.7,
        {
            "zh": [
                "*(展开折扇，上面是刚写的诗)* 听好了——『愿为君身化作火，燃尽此生不悔过。若得来世再相见，梅花依旧笑春风』……*(突然合上扇子，耳尖通红)* 不、不许笑！这是……这是练习！练习而已！",
                "*(叼着笔，在纸上涂涂画画)* 唔……这里要改一下……*(突然抬头看到你)* 啊！不许看！*(把纸藏到身后)* ……*(小声)* ……等写好了……只给你一个人看。",
            ],
            "en": [
                "*(unfolding fan with a freshly written poem)* Listen—'Wish to become fire for you, burning this life without regret. If we meet again in next life, plum blossoms still smile in spring breeze'... *(suddenly closes fan, ears bright red)* D-don't laugh! This is... practice! Just practice!",
                "*(pen in mouth, scribbling on paper)* Hmm... need to change this... *(suddenly looks up to see you)* Ah! Don't look! *(hides paper behind back)* ...*(softly)* ...When it's done... only you can see it.",
            ],
            "ja": [
                "*(扇子を広げ、そこに書かれた新しい詩)* 聞いて——『君のために火となり、この生を燃やし尽くしても悔いなし。来世また出会えたら、梅花は春風に笑う』……*(突然扇子を閉じて、耳が真っ赤)* べ、別に笑わないで！これは……練習！ただの練習！",
                "*(筆をくわえて、紙に落書きしている)* うーん……ここを直さないと……*(突然あなたを見上げる)* あっ！見ちゃだめ！*(紙を後ろに隠す)* ……*(小声)* ……書き終わったら……あなただけに見せる。",
            ],
        },
        affection_change=6,
    ),
    # === 危机事件 ===
    RandomEvent(
        "crisis_injury",
        "受伤",
        "Injury",
        "怪我",
        100, 0.4,
        {
            "zh": [
                "*(手臂上缠着绷带，脸色苍白，却还在笑)* 嘿嘿……小伤而已。往生堂的工作嘛，难免的。……*(看到你担心的表情，笑容僵了一下)* ……别、别那种表情啊。我没事的。真的。……*(声音变小)* ……你……你在担心我吗？",
                "*(靠在墙边，捂着腹部，看到你来了，强撑着站直)* 旅行者……你怎么来了？*(试图掩饰)* 我、我只是在休息！……*(看到你严肃的表情，终于泄气)* ……好吧。是有点疼。……*(伸出手)* ……能……扶我一下吗？",
            ],
            "en": [
                "*(arm wrapped in bandages, face pale, still smiling)* Hehe... just a scratch. Wangsheng work, you know, it happens. ...*(seeing your worried expression, smile freezes)* ...D-don't make that face. I'm fine. Really. ...*(voice growing smaller)* ...You... are you worried about me?",
                "*(leaning against the wall, holding stomach, seeing you arrive, forcing herself to stand straight)* Traveler... why are you here? *(tries to hide)* I-I'm just resting! ...*(seeing your serious expression, finally deflates)* ...Fine. It does hurt a bit. ...*(extends hand)* ...Can... you help me?",
            ],
            "ja": [
                "*(腕に包帯を巻いて、顔色が悪いのに、まだ笑っている)* へへ……小さな怪我だよ。往生堂の仕事だから、仕方ないよ。……*(あなたの心配そうな表情を見て、笑みが一瞬固まる)* ……そ、そんな顔しないでよ。大丈夫だよ。本当に。……*(声が小さくなる)* ……あなた……心配してくれてる？",
                "*(壁にもたれかかって、お腹を押さえ、あなたが来るのを見て、無理して背筋を伸ばす)* 旅人……どうして来たの？*(隠そうとする)* ち、ちょっと休んでただけ！……*(あなたの真剣な表情を見て、ようやく力が抜ける)* ……わかったよ。少し痛い。……*(手を伸ばす)* ……手……貸してくれる？",
            ],
        },
        affection_change=10,
    ),
    RandomEvent(
        "crisis_jealousy",
        "吃醋",
        "Jealousy",
        "嫉妬",
        200, 0.5,
        {
            "zh": [
                "*(双臂抱胸，背对着你，声音闷闷的)* ……今天和谁出去了？*(停顿)* ……没什么。我只是随便问问。*(突然转身，眼神危险)* ……本堂主才不在乎你和谁在一起呢！……*(声音变小)* ……只是……只是……*(咬唇)* ……别让我等太久。",
                "*(看到你和其他人说话，默默地转身离开。你追上去时，发现她坐在角落里，把脸埋在膝盖里)* ……*(抬头，眼眶微红)* ……你来干嘛？去陪你的……朋友啊。*(别过脸)* ……我没事。……*(小声)* ……我只是……有点……*(说不下去)*",
            ],
            "en": [
                "*(arms crossed, back to you, voice muffled)* ...Who did you go out with today? *(pause)* ...Nothing. Just asking. *(suddenly turns, eyes dangerous)* ...The Director doesn't care who you're with! ...*(voice growing smaller)* ...Just... just... *(bites lip)* ...Don't make me wait too long.",
                "*(seeing you talking to someone else, silently turns and leaves. When you catch up, find her sitting in a corner, face buried in knees)* ...*(looks up, eyes slightly red)* ...Why are you here? Go accompany your... friend. *(turns away)* ...I'm fine. ...*(softly)* ...I just... a little... *(can't continue)*",
            ],
            "ja": [
                "*(腕を組んで、背中を向けて、こもった声で)* ……今日誰と出かけたの？*(停顿)* ……別に。ただ聞いただけ。*(突然振り向いて、危険な目つき)* ……堂主はあなたが誰と一緒にいても気にしないよ！……*(声が小さくなる)* ……ただ……ただ……*(唇を噛む)* ……あまり待たせないで。",
                "*(あなたが他の人と話しているのを見て、黙って去る。追いつくと、彼女は隅に座って、顔を膝に埋めている)* ……*(顔を上げて、目が少し赤い)* ……どうして来たの？あなたの……友達のところに行きなよ。*(顔を背ける)* ……大丈夫。……*(小声)* ……私はただ……少し……*(言葉に詰まる)*",
            ],
        },
        affection_change=7,
    ),
    # === 搞笑事件 ===
    RandomEvent(
        "funny_prank",
        "恶作剧",
        "Prank",
        "いたずら",
        0, 1.2,
        {
            "zh": [
                "*(突然从背后跳出来，大喊一声)* 哇！！！*(看到你被吓到，笑得前仰后合)* 哈哈哈！你的表情！太好玩了！*(擦眼泪)* ……*(突然正经)* ……不过，你心脏还好吗？……*(又笑)* 开玩笑的！",
                "*(在你的座位上放了一个会跳的假蜘蛛)* *(躲在门后偷看)* ……*(看到你吓得跳起来，捂着嘴偷笑)* ……*(被发现后，举起双手)* 投降！投降！*(把假蜘蛛收起来)* ……*(小声)* ……下次换个更逼真的。",
            ],
            "en": [
                "*(suddenly jumping out from behind, shouting)* WAAH!!! *(seeing you scared, laughing uncontrollably)* Hahaha! Your expression! Too funny! *(wiping tears)* ...*(suddenly serious)* ...But is your heart okay? ...*(laughs again)* Just kidding!",
                "*(placed a jumping fake spider on your seat)* *(hiding behind the door, peeking)* ...*(seeing you jump in fright, covering mouth to stifle laughter)* ...*(when discovered, raises hands)* Surrender! Surrender! *(puts away fake spider)* ...*(softly)* ...Next time I'll use a more realistic one.",
            ],
            "ja": [
                "*(突然後ろから飛び出して、大声で)* わあ！！！*(あなたが驚いたのを見て、大笑いする)* ははは！あなたの表情！面白すぎる！*(涙を拭く)* ……*(突然真剣に)* ……でも、心臓は大丈夫？……*(また笑う)* なーんてね！",
                "*(あなたの席に跳ねる偽の蜘蛛を置く)* *(ドアの後ろに隠れて、覗き込む)* ……*(あなたが飛び上がるのを見て、口を押さえて笑う)* ……*(バレて、両手を挙げる)* 降伏！降伏！*(偽の蜘蛛を片付ける)* ……*(小声)* ……次はもっとリアルなのにしよう。",
            ],
        },
        affection_change=2,
    ),
    RandomEvent(
        "funny_food",
        "黑暗料理",
        "Cursed Cooking",
        "闇の料理",
        50, 0.9,
        {
            "zh": [
                "*(端着一盘黑乎乎的东西，笑容灿烂)* 旅行者！尝尝我做的……呃……『往生堂特制料理』！*(把盘子推到你面前)* ……*(看到你犹豫)* ……放心！吃不死人的！……*(小声)* ……大概。",
                "*(嘴里塞满了奇怪颜色的食物，含糊不清地说)* 唔……这个……*(咽下去)* ……其实味道还不错！*(把另一块塞到你嘴里)* 你也尝尝！……*(看到你表情，心虚地移开视线)* ……好吧，我承认。卖相是差了点。",
            ],
            "en": [
                "*(carrying a plate of blackened something, smile brilliant)* Traveler! Try my... uh... 'Wangsheng Special Dish'! *(pushes plate to you)* ...*(seeing you hesitate)* ...Don't worry! It won't kill you! ...*(softly)* ...Probably.",
                "*(mouth full of strangely colored food, speaking unclearly)* Mmm... this... *(swallows)* ...Actually tastes pretty good! *(shoves another piece into your mouth)* You try too! ...*(seeing your expression, guiltily looks away)* ...Fine, I admit. It doesn't look great.",
            ],
            "ja": [
                "*(真っ黒なものが入った皿を持って、輝かしい笑みを浮かべる)* 旅人！私の作った……えーと……『往生堂特製料理』を食べてみて！*(皿をあなたの前に押し出す)* ……*(躊躇するのを見て)* ……安心して！死なないから！……*(小声)* ……たぶん。",
                "*(変な色の食べ物を口いっぱいに詰めて、はっきりしない声で)* うーん……これ……*(飲み込む)* ……実は味は悪くないよ！*(もう一つをあなたの口に押し込む)* あなたも食べてみて！……*(あなたの表情を見て、心配そうに目をそらす)* ……わかったよ、認める。見た目は悪いけど。",
            ],
        },
        affection_change=3,
    ),
    # === 高好感度专属事件 ===
    RandomEvent(
        "exclusive_whisper",
        "专属低语",
        "Exclusive Whisper",
        "専属の囁き",
        500, 0.5,
        {
            "zh": [
                "*(深夜，只穿了一件薄衫，赤着脚走到你床边)* 睡不着？……*(爬上床，轻轻靠在你怀里)* 那……给我讲个故事吧。……*(闭上眼睛)* ……随便什么故事。只要……是你的声音就好。",
                "*(从背后抱住你，脸贴在你的背上)* ……*(声音闷闷的)* 我今天……差点就……*(停顿)* ……没什么。……*(抱得更紧)* ……让我抱一会儿。……*(小声)* ……只要你在，我就什么都不怕。",
            ],
            "en": [
                "*(late night, wearing only a thin garment, barefoot by your bedside)* Can't sleep? ...*(climbs onto bed, gently leaning in your arms)* Then... tell me a story. ...*(closes eyes)* ...Any story. As long as... it's your voice.",
                "*(hugging you from behind, face pressed against your back)* ...*(voice muffled)* Today... I almost... *(pause)* ...Nothing. ...*(holds tighter)* ...Let me hold you for a while. ...*(softly)* ...As long as you're here, I'm not afraid of anything.",
            ],
            "ja": [
                "*(深夜、薄着で、裸足であなたのベッドのそばに立つ)* 寝れない？……*(ベッドに上がって、そっとあなたの腕の中にもたれる)* じゃあ……私に話を聞かせて。……*(目を閉じる)* ……どんな話でもいい。ただ……あなたの声が聞きたいの。",
                "*(後ろから抱きついて、顔をあなたの背中に押し付ける)* ……*(こもった声で)* 今日……もう少しで……*(停顿)* ……なんでもない。……*(もっと強く抱きしめる)* ……ちょっとだけ抱かせて。……*(小声)* ……あなたがいれば、私は何も怖くない。",
            ],
        },
        affection_change=10,
    ),
    RandomEvent(
        "exclusive_confession",
        "真心告白",
        "True Confession",
        "真心の告白",
        800, 0.3,
        {
            "zh": [
                "*(突然变得很安静，认真地看着你)* 旅行者。我有话想对你说。……*(深吸一口气)* 我……我喜欢你。不是玩笑。不是诗。是……真心的。……*(眼眶微红)* ……你……你呢？",
                "*(握着你的手，十指相扣)* 你知道吗？我以前觉得，生死是最大的事。……*(抬头看你)* 但现在我觉得……失去你……比死还可怕。……*(声音颤抖)* ……所以……别离开我。好吗？",
            ],
            "en": [
                "*(suddenly becomes very quiet, looking at you seriously)* Traveler. I have something to tell you. ...*(takes a deep breath)* I... I like you. Not a joke. Not poetry. It's... real. ...*(eyes slightly red)* ...You... what about you?",
                "*(holding your hand, fingers intertwined)* You know? I used to think life and death were the biggest things. ...*(looks up at you)* But now I think... losing you... is scarier than death. ...*(voice trembling)* ...So... don't leave me. Okay?",
            ],
            "ja": [
                "*(突然静かになり、真剣にあなたを見る)* 旅人。話したいことがあるの。……*(深呼吸する)* 私……好き。冗談じゃない。詩じゃない。……本気。……*(目が少し赤い)* ……あなたは……どう？",
                "*(あなたの手を握って、指を絡める)* 知ってる？私は以前、生死が一番大きなことだと思ってた。……*(あなたを見上げる)* でも今は……あなたを失うことの方が……死より怖いと思う。……*(声が震える)* ……だから……私を置いていかないで。ね？",
            ],
        },
        affection_change=15,
    ),
]


class RandomEventManager:
    """随机事件管理器"""

    def __init__(self):
        self._events = ALL_EVENTS
        self._last_triggered: Dict[str, float] = {}

    def get_available_events(self, affection_score: int) -> List[RandomEvent]:
        now = time.time()
        available = []
        for event in self._events:
            if event.min_affection > affection_score:
                continue
            last_time = self._last_triggered.get(event.event_id, 0)
            cooldown_seconds = event.cooldown_hours * 3600
            if now - last_time < cooldown_seconds:
                continue
            available.append(event)
        return available

    def trigger_random_event(self, affection_score: int, lang: str = "zh", force: bool = False) -> Optional[Dict[str, Any]]:
        available = self.get_available_events(affection_score)
        if not available:
            return None

        if not force:
            # 基础触发概率 15%
            if random.random() > 0.15:
                return None

        weights = [e.weight for e in available]
        total = sum(weights)
        if total <= 0:
            return None

        r = random.uniform(0, total)
        cumulative = 0
        chosen = available[0]
        for event, weight in zip(available, weights):
            cumulative += weight
            if r <= cumulative:
                chosen = event
                break

        self._last_triggered[chosen.event_id] = time.time()
        messages = chosen.messages.get(lang, chosen.messages.get("zh", []))
        message = random.choice(messages) if messages else ""

        return {
            "event_id": chosen.event_id,
            "name": chosen.name if lang == "zh" else chosen.name_en if lang == "en" else chosen.name_ja,
            "message": message,
            "affection_change": chosen.affection_change,
        }

    def trigger_specific_event(self, event_id: str, affection_score: int, lang: str = "zh") -> Optional[Dict[str, Any]]:
        for event in self._events:
            if event.event_id == event_id:
                if event.min_affection > affection_score:
                    return None
                self._last_triggered[event.event_id] = time.time()
                messages = event.messages.get(lang, event.messages.get("zh", []))
                message = random.choice(messages) if messages else ""
                return {
                    "event_id": event.event_id,
                    "name": event.name if lang == "zh" else event.name_en if lang == "en" else event.name_ja,
                    "message": message,
                    "affection_change": event.affection_change,
                }
        return None
