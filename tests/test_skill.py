"""Hu Tao Dual Mode Skill - Test Suite v3.0"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hutao_skill.affection import AffectionSystem, get_level_by_score
from hutao_skill.emotion_manager import EmotionManager
from hutao_skill.events import MinigameManager, SeasonalEventManager
from hutao_skill.memory import EmotionMemory, MemoryEntry
from hutao_skill.performance import PerformanceTracker
from hutao_skill.prompts import get_emotion_state_addition, get_system_prompt
from hutao_skill.random_events import RandomEventManager


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
        self.sfw_manager = EmotionManager(self.config_path, mode="sfw")
        self.nsfw_manager = EmotionManager(self.config_path, mode="nsfw")

    def test_load_sfw_states(self):
        states = self.sfw_manager.get_all_states()
        self.assertEqual(len(states), 3)
        self.assertIn("引魂", states)
        self.assertIn("守墓", states)
        self.assertIn("幽冥", states)

    def test_load_nsfw_states(self):
        states = self.nsfw_manager.get_all_states()
        self.assertEqual(len(states), 3)
        self.assertIn("欲火", states)
        self.assertIn("占有", states)
        self.assertIn("蚀骨", states)

    def test_mode_switch(self):
        self.assertEqual(self.sfw_manager.mode, "sfw")
        self.sfw_manager.mode = "nsfw"
        self.assertEqual(self.sfw_manager.mode, "nsfw")
        states = self.sfw_manager.get_all_states()
        self.assertIn("欲火", states)

    def test_detect_emotion_sfw(self):
        result = self.sfw_manager.detect_emotion("诗")
        self.assertIsNotNone(result)
        result = self.sfw_manager.detect_emotion("孤独")
        self.assertIsNotNone(result)

    def test_detect_emotion_nsfw(self):
        result = self.nsfw_manager.detect_emotion("想要你")
        self.assertIsNotNone(result)
        result = self.nsfw_manager.detect_emotion("温柔")
        self.assertIsNotNone(result)


class TestPrompts(unittest.TestCase):
    def test_sfw_system_prompt(self):
        prompt = get_system_prompt("zh", "sfw")
        self.assertGreater(len(prompt), 0)
        self.assertIn("全年龄", prompt)

    def test_nsfw_system_prompt(self):
        prompt = get_system_prompt("zh", "nsfw")
        self.assertGreater(len(prompt), 0)
        self.assertIn("欲望", prompt)

    def test_sfw_emotion_addition(self):
        addition = get_emotion_state_addition("引魂", "zh", "sfw")
        self.assertGreater(len(addition), 0)

    def test_nsfw_emotion_addition(self):
        addition = get_emotion_state_addition("欲火", "zh", "nsfw")
        self.assertGreater(len(addition), 0)


class TestMemory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "memory.json")
        self.memory = EmotionMemory(max_entries=10, storage_path=self.storage_path, auto_cleanup=False)

    def tearDown(self):
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
        os.rmdir(self.temp_dir)

    def test_add_memory_with_mode(self):
        self.memory.add(user_message="测试", bot_response="回应", form="引魂", mode="sfw")
        self.assertEqual(self.memory.memory_count, 1)

    def test_generate_diary_sfw(self):
        for i in range(5):
            self.memory.add(user_message=f"消息{i}", bot_response=f"回复{i}", form="引魂", mode="sfw")
        diary = self.memory.generate_diary(mode="sfw")
        self.assertIsInstance(diary, str)
        self.assertGreater(len(diary), 0)

    def test_generate_diary_nsfw(self):
        for i in range(5):
            self.memory.add(user_message=f"消息{i}", bot_response=f"回复{i}", form="欲火", mode="nsfw")
        diary = self.memory.generate_diary(mode="nsfw")
        self.assertIsInstance(diary, str)
        self.assertGreater(len(diary), 0)


class TestAffection(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "affection.json")
        self.affection = AffectionSystem(storage_path=self.storage_path)

    def tearDown(self):
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
        os.rmdir(self.temp_dir)

    def test_initial_score(self):
        self.assertEqual(self.affection.score, 0)

    def test_add_score(self):
        self.affection.add_score(10, "test")
        self.assertEqual(self.affection.score, 10)

    def test_level_progression(self):
        self.affection.add_score(60, "test")
        self.assertEqual(self.affection.current_level.name, "朋友")

    def test_checkin(self):
        record = self.affection.checkin()
        self.assertIsNotNone(record)
        self.assertGreater(record.score_gained, 0)
        self.assertEqual(self.affection.checkin_streak, 1)

    def test_duplicate_checkin(self):
        self.affection.checkin()
        record = self.affection.checkin()
        self.assertIsNone(record)

    def test_get_level_by_score(self):
        level = get_level_by_score(5)
        self.assertEqual(level.min_score, 0)
        self.assertEqual(level.max_score, 9)
        level = get_level_by_score(100)
        self.assertEqual(level.min_score, 50)
        self.assertEqual(level.max_score, 149)
        level = get_level_by_score(600)
        self.assertEqual(level.min_score, 500)
        self.assertEqual(level.max_score, 799)


class TestRandomEvents(unittest.TestCase):
    def setUp(self):
        self.manager = RandomEventManager()

    def test_get_available_events(self):
        events = self.manager.get_available_events(0)
        self.assertGreater(len(events), 0)

    def test_trigger_random_event(self):
        result = self.manager.trigger_random_event(0, "zh", force=True)
        self.assertIsNotNone(result)
        self.assertIn("message", result)

    def test_high_affection_events(self):
        events = self.manager.get_available_events(1000)
        event_ids = [e.event_id for e in events]
        self.assertIn("exclusive_whisper", event_ids)
        self.assertIn("exclusive_confession", event_ids)


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
        self.assertEqual(self.skill.version, "3.0.0")
        self.assertEqual(self.skill.language, "zh")

    def test_default_mode(self):
        self.assertEqual(self.skill._mode, "sfw")

    def test_night_mode_detection(self):
        self.assertTrue(hasattr(self.skill, '_is_night_mode'))

    def test_contract_system(self):
        self.assertFalse(self.skill._soul_contract_active)

    def test_affection_system(self):
        self.assertIsNotNone(self.skill._affection)
        self.assertEqual(self.skill._affection.score, 0)

    def test_mode_switch(self):
        msg = self.skill._switch_mode("nsfw")
        self.assertEqual(self.skill._mode, "nsfw")
        # Check that message is not empty and mode actually changed
        self.assertGreater(len(msg), 0)
        self.assertNotEqual(self.skill._mode, "sfw")

    def test_get_state_info(self):
        info = self.skill.get_current_state_info()
        self.assertIn("mode", info)
        self.assertIn("affection_score", info)


if __name__ == "__main__":
    unittest.main(verbosity=2)
