# Hu Tao Soul Awakening - API 文档

## 主类：HuTaoSoulAwakening

### 构造函数

```python
HuTaoSoulAwakening(config_path: Optional[str] = None)
```

参数：
- `config_path` - 配置文件路径，默认使用 `hutao_skill/config.json`

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | str | Skill 名称 |
| `description` | str | Skill 描述 |
| `version` | str | 版本号 |
| `language` | str | 当前语言（zh/en/ja） |
| `current_emotion` | str | 当前心境（嬉皮/哲思/庄严） |
| `auto_shift_probability` | float | 自动心境波动概率（默认 0.15） |
| `proactive_chat_enabled` | bool | 主动聊天开关 |

### 命令处理器

#### `@on_message()` - handle_message

处理普通消息，自动进行心境检测、关键词响应、主动聊天等。

#### `@on_command("心境")` - cmd_emotion

查看当前心境状态。

#### `@on_command("属性")` - cmd_stats

查看胡桃角色属性面板。

#### `@on_command("语言")` - cmd_language

切换语言。参数：`zh` / `en` / `ja`

#### `@on_command("日记")` - cmd_diary

生成对话日记（诗集风格）。

#### `@on_command("清空记忆")` - cmd_clear_memory

清空情感记忆。

#### `@on_command("小游戏")` - cmd_minigame

玩互动小游戏。参数：`对诗` / `捉鬼` / `往生`

#### `@on_command("主动聊天")` - cmd_proactive_chat

开启/关闭主动聊天。参数：`开` / `关`

#### `@on_command("帮助")` - cmd_help

显示帮助信息。

### 公共 API

#### `record_interaction(user_message, bot_response, emotion_score=0.0, keywords=None)`

记录一次交互到情感记忆。

#### `get_memory_summary()` -> str

获取记忆摘要。

#### `get_current_state_info()` -> dict

获取当前状态信息。

#### `get_performance_stats()` -> dict

获取性能统计。

---

## EmotionManager

### 方法

#### `detect_emotion(message: str) -> Optional[str]`

基于消息内容检测心境状态，返回得分最高的心境名称。

#### `get_all_states() -> List[str]`

获取所有心境状态名称。

#### `get_state(name: str) -> Optional[EmotionState]`

获取指定心境状态。

#### `get_state_stats_display(state_name: str, lang: str = "zh") -> str`

获取心境状态展示文本。

---

## EmotionMemory

### 方法

#### `add(user_message, bot_response, form, emotion_score=0.0, keywords=None)`

添加一条新记忆。

#### `get_recent(n: int = 5) -> List[MemoryEntry]`

获取最近 n 条记忆。

#### `get_memory_summary() -> str`

生成记忆摘要，用于注入系统提示词。

#### `generate_diary() -> str`

生成日记摘要（胡桃诗集风格）。

#### `clear()`

清空所有记忆。

#### `set_preference(key, value)`

设置用户偏好。

#### `get_preference(key, default=None)`

获取用户偏好。

---

## MinigameManager

### 方法

#### `play_poetry_game(lang: str = "zh") -> str`

对诗小游戏。

#### `play_ghost_game(lang: str = "zh") -> str`

捉鬼小游戏。

#### `play_ritual_game(lang: str = "zh") -> str`

往生仪式小游戏。

---

## SeasonalEventManager

### 方法

#### `get_event_message(lang: str = "zh") -> Optional[str]`

获取当前日期的特殊事件消息。

---

## Prompts（模块函数）

#### `get_system_prompt(lang: str = "zh") -> str`

获取系统提示词。

#### `get_emotion_state_addition(emotion: str, lang: str = "zh") -> str`

获取心境状态追加提示词。

#### `reload_prompts()`

热重载提示词配置。
