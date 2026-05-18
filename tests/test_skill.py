"""Hu Tao Soul Awakening Skill - Test Suite

测试套件涵盖：
- Skill 初始化
- 心境检测
- 情感关键词
- 季节事件
- 小游戏
- 记忆系统
- 命令处理
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hutao_skill.emotion_manager import EmotionManager, EmotionState
from hutao_skill.events import MinigameManager, SeasonalEventManager
from hutao_skill.memory import EmotionMemory, MemoryEntry
from hutao_skill.performance import PerformanceTracker
from hutao_skill.prompts import (
    get_emotion_state_addition,
    get_system_prompt,
    reload_prompts,
)


class MockContext:
    """Mock OpenClaw context for testing"""

    def __init__(self, message="", user_id="test_user"):
        self.message = message
        self.user_id = user_id
        self._system_prompt = None
        self._sent_messages = []

    def set_system_prompt(self, prompt):
        self._system_prompt = prompt

    def send(self, message):
        self._sent_messages.append(message)

    def get_args(self):
        return self.message


class TestEmotionManager(unittest.TestCase):
    """测试心境管理器"""

    def setUp(self):
        self.config_path = os.path.join(
            os.path.dirname(__file__), "..", "hutao_skill", "config.json"
        )
        self.manager = EmotionManager(self.config_path)

    def test_load_states(self):
        """测试加载心境状态"""
        states = self.manager.get_all_states()
        self.assertEqual(len(states), 3)
        self.assertIn("嬉皮", states)
        self.assertIn("哲思", states)
        self.assertIn("庄严", states)

    def test_detect_emotion(self):
        """测试心境检测"""
        # 应该检测到嬉皮
        result = self.manager.detect_emotion("我们来开玩笑吧！")
        self.assertEqual(result, "嬉皮")

        # 应该检测到哲思
        result = self.manager.detect_emotion("生命的意义是什么？")
        self.assertEqual(result, "哲思")

        # 应该检测到庄严
        result = self.manager.detect_emotion("往生堂的规矩是什么？")
        self.assertEqual(result, "庄严")

    def test_get_state(self):
        """测试获取心境状态"""
        state = self.manager.get_state("嬉皮")
        self.assertIsNotNone(state)
        self.assertIsInstance(state, EmotionState)
        self.assertEqual(state.name, "嬉皮")

    def test_get_state_stats_display(self):
        """测试状态展示文本"""
        display = self.manager.get_state_stats_display("嬉皮", "zh")
        self.assertIn("嬉皮", display)
        self.assertIn("标签", display)


class TestMemory(unittest.TestCase):
    """测试情感记忆系统"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "memory.json")
        self.memory = EmotionMemory(
            max_entries=10,
            storage_path=self.storage_path,
            auto_cleanup=False,
        )

    def tearDown(self):
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
        os.rmdir(self.temp_dir)

    def test_add_memory(self):
        """测试添加记忆"""
        self.memory.add(
            user_message="你好胡桃！",
            bot_response="你好旅行者！",
            form="嬉皮",
        )
        self.assertEqual(self.memory.memory_count, 1)

    def test_get_recent(self):
        """测试获取最近记忆"""
        for i in range(5):
            self.memory.add(
                user_message=f"消息{i}",
                bot_response=f"回复{i}",
                form="嬉皮",
            )
        recent = self.memory.get_recent(3)
        self.assertEqual(len(recent), 3)

    def test_memory_summary(self):
        """测试记忆摘要"""
        self.memory.add(
            user_message="测试消息",
            bot_response="测试回复",
            form="嬉皮",
        )
        summary = self.memory.get_memory_summary()
        self.assertIn("Recent Memories", summary)

    def test_generate_diary(self):
        """测试日记生成"""
        for i in range(5):
            self.memory.add(
                user_message=f"消息{i}",
                bot_response=f"回复{i}",
                form="嬉皮",
            )
        diary = self.memory.generate_diary()
        self.assertIn("胡桃的诗集", diary)
        self.assertIn("今天和旅行者聊了", diary)

    def test_clear_memory(self):
        """测试清空记忆"""
        self.memory.add(
            user_message="测试",
            bot_response="回复",
            form="嬉皮",
        )
        self.memory.clear()
        self.assertEqual(self.memory.memory_count, 0)

    def test_preferences(self):
        """测试用户偏好"""
        self.memory.set_preference("language", "zh")
        self.assertEqual(self.memory.get_preference("language"), "zh")
        self.assertEqual(self.memory.get_preference("unknown", "default"), "default")


class TestEvents(unittest.TestCase):
    """测试事件和小游戏"""

    def setUp(self):
        self.config_path = os.path.join(
            os.path.dirname(__file__), "..", "hutao_skill", "config.json"
        )
        self.event_manager = SeasonalEventManager(self.config_path)
        self.minigame_manager = MinigameManager(self.config_path)

    def test_list_games(self):
        """测试列出游戏"""
        games = self.minigame_manager.list_games("zh")
        self.assertIn("对诗", games)
        self.assertIn("捉鬼", games)
        self.assertIn("往生", games)

    def test_play_poetry_game(self):
        """测试对诗游戏"""
        result = self.minigame_manager.play_poetry_game("zh")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_play_ghost_game(self):
        """测试捉鬼游戏"""
        result = self.minigame_manager.play_ghost_game("zh")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_play_ritual_game(self):
        """测试往生仪式游戏"""
        result = self.minigame_manager.play_ritual_game("zh")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class TestPerformance(unittest.TestCase):
    """测试性能追踪器"""

    def test_track_operation(self):
        """测试追踪操作"""
        tracker = PerformanceTracker(enabled=True, slow_threshold=1.0)
        with tracker.track("test_op"):
            pass
        stats = tracker.get_stats("test_op")
        self.assertIsNotNone(stats)
        self.assertEqual(stats["count"], 1)

    def test_disabled_tracker(self):
        """测试禁用追踪"""
        tracker = PerformanceTracker(enabled=False)
        with tracker.track("test_op"):
            pass
        stats = tracker.get_stats("test_op")
        self.assertIsNone(stats)


class TestPrompts(unittest.TestCase):
    """测试提示词加载"""

    def test_get_system_prompt(self):
        """测试获取系统提示词"""
        prompt = get_system_prompt("zh")
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 0)
        self.assertIn("胡桃", prompt)

    def test_get_emotion_addition(self):
        """测试获取心境追加内容"""
        addition = get_emotion_state_addition("嬉皮", "zh")
        self.assertIsInstance(addition, str)
        self.assertIn("鬼马精灵", addition)


class TestSkillIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # 复制 config.json 到临时目录
        import shutil

        src_config = os.path.join(
            os.path.dirname(__file__), "..", "hutao_skill", "config.json"
        )
        dst_config = os.path.join(self.temp_dir, "config.json")
        shutil.copy(src_config, dst_config)

        # 复制 prompts.json
        src_prompts = os.path.join(
            os.path.dirname(__file__), "..", "hutao_skill", "prompts.json"
        )
        dst_prompts = os.path.join(self.temp_dir, "prompts.json")
        shutil.copy(src_prompts, dst_prompts)

        from hutao_skill.hutao_skill import HuTaoSoulAwakening

        self.skill = HuTaoSoulAwakening(config_path=dst_config)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """测试 Skill 初始化"""
        self.assertEqual(self.skill.name, "HuTao_Soul_Awakening_Skill")
        self.assertEqual(self.skill.version, "1.0.0")
        self.assertEqual(self.skill.language, "zh")
        self.assertEqual(self.skill.current_emotion, "嬉皮")

    def test_current_state_info(self):
        """测试获取当前状态"""
        info = self.skill.get_current_state_info()
        self.assertIn("emotion", info)
        self.assertIn("language", info)
        self.assertEqual(info["emotion"], "嬉皮")

    def test_record_interaction(self):
        """测试记录交互"""
        self.skill.record_interaction(
            user_message="你好",
            bot_response="你好旅行者！",
        )
        summary = self.skill.get_memory_summary()
        self.assertIn("Recent Memories", summary)


if __name__ == "__main__":
    unittest.main(verbosity=2)
