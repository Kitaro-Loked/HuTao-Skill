# HuTao-Skill 🔥 v1.0

> 胡桃·阴阳两界灵魂觉醒（统一角色心境状态系统）：嬉皮 / 哲思 / 庄严

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

## ✨ 简介

这是一个为 [OpenClaw](https://github.com/openclaw) 框架设计的 Skill，让你的 AI 助手化身《原神》中的胡桃！

**v1.0 特性**：统一角色心境状态系统——胡桃作为一个完整的角色，根据对话内容自然流动心境（嬉皮/哲思/庄严）。这更符合胡桃的角色设定！

| 心境状态 | 触发场景 | 表现 |
|----------|----------|------|
| 🔥 **嬉皮** | 聊到玩笑、诗、恶作剧、搞笑 | 更加鬼马精灵，爱开玩笑和恶作剧 |
| 📜 **哲思** | 聊到生死、哲学、记忆、灵魂 | 更加诗意深沉，带着哲思和温柔 |
| 🕯️ **庄严** | 聊到职责、规矩、仪式、往生堂 | 更加严肃庄重，展现堂主的专业 |

## 🚀 安装

### 方式一：通过 OpenClaw 安装（推荐）

```bash
openclaw skill install https://github.com/Kitaro-Loked/HuTao-Skill
```

### 方式二：手动安装

```bash
git clone https://github.com/Kitaro-Loked/HuTao-Skill.git
cd HuTao-Skill
pip install -r requirements.txt
```

然后将 `hutao_skill/` 目录复制到你的 OpenClaw skills 目录中。

## 📖 使用方法

### 心境状态流动

胡桃的心境会根据对话内容**自然流动**，不需要手动切换：
- 提到「玩笑、诗、恶作剧、搞笑」→ 胡桃变得更加**鬼马精灵**
- 提到「生死、哲学、记忆、灵魂」→ 胡桃变得更加**诗意深沉**
- 提到「职责、规矩、仪式、往生堂」→ 胡桃变得更加**严肃庄重**

**15%** 的概率会自然心境波动，胡桃会发送心境变化的提示！

### 查看当前心境

```
心境
```

显示当前心境状态和相关信息：
```
当前心境：嬉皮
**嬉皮** 
🏷️ 标签: 鬼马, 精灵, 俏皮, 狡黠
🔑 关键词: 玩笑, 诗, 搞笑, 玩, 有趣...
```

### 查看胡桃属性

```
属性
```

显示胡桃的角色属性面板：
```
📊 胡桃属性
**胡桃** (往生堂七十七代堂主 · 火)
🛡️ 防御: 65 | ❤️ 生命: 75
⚡ 速度: 80 | ⚔️ 攻击: 85
🎯 暴击: 30%
```

### 多语言切换

```
语言 zh    # 中文
语言 en    # English
语言 ja    # 日本語
```

### 情感记忆与日记

胡桃会自动记录你们的对话历史，并定期生成诗集：

```
日记
```

**示例日记：**
> *(坐在往生堂的案前，轻轻翻开诗集，笔尖在纸上沙沙作响)*
>
> **胡桃的诗集** 📖
> 日期：2026年05月18日
> 天气：晴朗
>
> 今天和旅行者聊了 5 次天。大多数时候我是「嬉皮」心境。
> 我们聊了很多关于「诗、玩笑」的话题。
> 今天写了几首好诗！和旅行者在一起的每一刻都像火焰一样热烈！🔥
>
> *(合上诗集，露出狡黠的笑容)* 明天也要一起写诗哦！🔥

### 互动小游戏

```
小游戏 对诗    # 对诗小游戏
小游戏 捉鬼    # 捉鬼小游戏
小游戏 往生    # 往生仪式小游戏
```

### 主动聊天系统

胡桃会主动找你聊天哦！可以控制开关：

```
主动聊天 开    # 开启主动聊天
主动聊天 关    # 关闭主动聊天
```

### 季节事件

在特定日期，胡桃会自动发送特殊台词：
- **7月15日** — 胡桃的生日 🔥
- **4月5日** — 清明节 🕯️
- **7月7日** — 七夕 🎋
- **12月31日** — 跨年 🔥
- **1月1日** — 新年 🎊

### 帮助

```
帮助
```

## 📁 文件结构

```
HuTao-Skill/
├── SKILL.md                          # Skill 说明文档
├── README.md                         # 本文件
├── LICENSE                           # MIT 许可证
├── requirements.txt                  # 依赖列表
├── docs/
│   └── API.md                        # API 文档
├── __init__.py                       # 包入口
├── hutao_skill/                      # Skill 主包
│   ├── __init__.py
│   ├── hutao_skill.py                # Skill 主类
│   ├── config.json                   # 配置文件
│   ├── prompts.json                  # 提示词配置（系统提示词、心境状态）⭐
│   ├── prompts.py                    # 提示词加载器（支持热重载）
│   ├── emotion_manager.py            # 心境状态管理器
│   ├── memory.py                     # 情感记忆系统
│   ├── events.py                     # 季节事件 & 小游戏
│   ├── performance.py                # 性能追踪器
│   └── data/
│       └── memory.json               # 记忆持久化文件
├── tests/                            # 测试目录
│   ├── __init__.py
│   └── test_skill.py                 # 完整测试套件
└── .github/                          # GitHub 配置
    ├── ISSUE_TEMPLATE/
    ├── workflows/
    │   └── ci.yml                    # CI 自动化测试
    └── PULL_REQUEST_TEMPLATE.md
```

## 🔧 自定义配置

### 修改提示词（无需改代码！）

编辑 `hutao_skill/prompts.json` 即可自定义：

```json
{
  "system_prompts": {
    "zh": "你的自定义胡桃提示词...",
    "en": "Your custom Hu Tao prompt...",
    "ja": "あなたのカスタム胡桃プロンプト..."
  },
  "emotion_states": {
    "嬉皮": {
      "trigger_keywords": ["玩笑", "诗", "搞笑"],
      "system_prompt_addition": {
        "zh": "你现在特别鬼马精灵！"
      }
    }
  }
}
```

修改后自动生效（或重启 Skill）！

### 修改配置

编辑 `hutao_skill/config.json` 即可自定义：

- **角色属性**：修改 `character.stats`
- **心境波动概率**：修改 `skill.auto_shift_probability`
- **主动聊天间隔**：修改 `skill.proactive_chat_interval`
- **情感关键词**：修改 `emotion_keywords`
- **季节事件**：修改 `seasonal_events`
- **小游戏内容**：修改 `minigames`

### 添加新语言

1. 在 `prompts.json` 的 `meta.supported_languages` 中添加语言代码
2. 为 `system_prompts` 和每个心境状态的 `system_prompt_addition` 添加新语言
3. 在 `config.json` 的季节事件消息中添加新语言

### 添加新心境状态

1. 在 `prompts.json` 的 `emotion_states` 中添加新心境状态的提示词
2. 在 `config.json` 的 `emotion_states` 中添加新心境的配置（关键词、标签）

## 📚 文档

- [SKILL.md](SKILL.md) - Skill 使用说明
- [docs/API.md](docs/API.md) - 详细 API 文档

## 📜 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

## 🙏 致谢

- 灵感来源于《原神》中的角色 **胡桃**
- 基于 [OpenClaw](https://github.com/openclaw) 框架开发
- 项目结构和设计参考了 [Yoimiya-Skill](https://github.com/Kitaro-Loked/Yoimiya-Skill) 和 [March7th-Skill](https://github.com/Kitaro-Loked/March7th-Skill)

---

> *"有人问我怕不怕死，我说怕，怕死之前没活够。"* —— 胡桃
