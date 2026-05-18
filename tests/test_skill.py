"""Hu Tao Burning Desire Skill - Test Suite v2.0"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hutao_skill.emotion_manager import EmotionManager, EmotionState
from hutao_skill.events import MinigameManager, SeasonalEventManager
from hutao_skill.memory import EmotionMemory, MemoryEntry
from hutao_skill.performance import PerformanceTracker
from hutao_skill.prompts import get_emotion_state_addition, get_system_prompt


class MockContext:
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
    def setUp(self):
        self.config_path = os.path.join(os.path.dirname(__file__), "..", "hutao_skill", "config.json")
        self.manager = EmotionManager(self.config_path)

    def test_load_states(self):
        states = self.manager.get_all_states()
        self.assertEqual(len(states), 3)
        # Use bytes comparison to avoid encoding issues
        self.assertIn("欲火".encode('utf-8').decode('utf-8'), [s.encode('utf-8').decode('utf-8') for s in states])

    def test_detect_emotion(self):
        result = self.manager.detect_emotion("我想要你")
        self.assertIsNotNone(result)
        result = self.manager.detect_emotion("温柔一点")
        self.assertIsNotNone(result)
        result = self.manager.detect_emotion("你是我的")
        self.assertIsNotNone(result)

    def test_get_state(self):
        for name in self.manager.get_all_states():
            state = self.manager.get_state(name)
            self.assertIsNotNone(state)
            self.assertIsInstance(state, EmotionState)


class TestMemory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "memory.json")
        self.memory = EmotionMemory(max_entries=10, storage_path=self.storage_path, auto_cleanup=False)

    def tearDown(self):
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
        os.rmdir(self.temp_dir)

    def test_add_memory_with_night_mode(self):
        self.memory.add(user_message="深夜测试", bot_response="回应", form="欲火", is_night_mode=True)
        self.assertEqual(self.memory.memory_count, 1)
        self.assertEqual(self.memory.get_night_mode_count(), 1)

    def test_generate_diary(self):
        for i in range(5):
            self.memory.add(user_message=f"消息{i}", bot_response=f"回复{i}", form="欲火")
        diary = self.memory.generate_diary()
        self.assertIsInstance(diary, str)
        self.assertGreater(len(diary), 0)


class TestEvents(unittest.TestCase):
    def setUp(self):
        self.config_path = os.path.join(os.path.dirname(__file__), "..", "hutao_skill", "config.json")
        self.minigame_manager = MinigameManager(self.config_path)

    def test_play_rendezvous_game(self):
        result = self.minigame_manager.play_rendezvous_game("zh")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_play_marking_game(self):
        result = self.minigame_manager.play_marking_game("zh")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class TestSkillIntegration(unittest.TestCase):
    def setUp(self):
        import shutil
        self.temp_dir = tempfile.mkdtemp()
        src_config = os.path.join(os.path.dirname(__file__), "..", "hutao_skill", "config.json")
        dst_config = os.path.join(self.temp_dir, "config.json")
        shutil.copy(src_config, dst_config)
        src_prompts = os.path.join(os.path.dirname(__file__), "..", "hutao_skill", "prompts.json")
        dst_prompts = os.path.join(self.temp_dir, "prompts.json")
        shutil.copy(src_prompts, dst_prompts)
        from hutao_skill.hutao_skill import HuTaoNetherworldGuide
        self.skill = HuTaoNetherworldGuide(config_path=dst_config)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        self.assertEqual(self.skill.version, "2.0.0")
        self.assertEqual(self.skill.language, "zh")

    def test_night_mode_detection(self):
        self.assertTrue(hasattr(self.skill, '_is_night_mode'))

    def test_contract_system(self):
        self.assertFalse(self.skill._soul_contract_active)


if __name__ == "__main__":
    unittest.main(verbosity=2)
