"""Unit test untuk modul jiwa/ (mood engine, events, personality)."""

import unittest
from unittest.mock import MagicMock

from jiwa.events import EventHandler, FACE_DETECTED, SHUTDOWN, SPEAKING_END, SPEAKING_START
from jiwa.mood import MoodEngine
from jiwa.personality import Personality
from nyawa.event_bus import Event, EventBus


class TestMoodEngine(unittest.TestCase):
    def test_initial_mood_is_idle(self):
        bus = EventBus()
        engine = MoodEngine(bus)
        self.assertEqual(engine.mood, "idle")
        self.assertEqual(engine.tick, 0)

    def test_trigger_face_detected_sets_happy(self):
        bus = EventBus()
        engine = MoodEngine(bus)
        engine.trigger(FACE_DETECTED)
        self.assertEqual(engine.mood, "happy")

    def test_trigger_touched_head_sets_excited(self):
        bus = EventBus()
        engine = MoodEngine(bus)
        engine.trigger("TOUCHED_HEAD")
        self.assertEqual(engine.mood, "excited")

    def test_unknown_event_does_not_crash(self):
        bus = EventBus()
        engine = MoodEngine(bus)
        engine.trigger("UNKNOWN_EVENT_XYZ")
        self.assertEqual(engine.mood, "idle")

    def test_update_increments_tick(self):
        bus = EventBus()
        engine = MoodEngine(bus)
        engine.update()
        engine.update()
        self.assertEqual(engine.tick, 2)


class TestPersonality(unittest.TestCase):
    def test_default_name_is_emo(self):
        p = Personality()
        self.assertEqual(p.name, "Emo")

    def test_say_returns_non_empty_for_known_mood(self):
        p = Personality()
        self.assertTrue(p.say("happy"))

    def test_say_returns_empty_for_unknown_mood(self):
        p = Personality()
        self.assertEqual(p.say("unknown_mood"), "")


class TestEventHandler(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()
        self.mood = MagicMock()
        self.speaker = MagicMock()
        self.tts = MagicMock()
        self.animator = MagicMock()
        self.handler = EventHandler(self.bus, self.mood, self.speaker, self.tts, self.animator)

    def test_face_detected_triggers_mood_and_sound(self):
        self.handler._handle(Event(type=FACE_DETECTED))
        self.mood.trigger.assert_called_once_with(FACE_DETECTED)
        self.speaker.play.assert_called_once_with("happy")

    def test_speaking_start_sets_talking_animation(self):
        self.handler._handle(Event(type=SPEAKING_START, data=0.7))
        self.animator.set_talking.assert_called_once_with(True, 0.7)

    def test_speaking_end_stops_talking_animation(self):
        self.handler._handle(Event(type=SPEAKING_END))
        self.animator.set_talking.assert_called_once_with(False, 0.0)

    def test_shutdown_stops_handler_loop(self):
        self.handler._running = True
        self.handler._handle(Event(type=SHUTDOWN))
        self.assertFalse(self.handler._running)


if __name__ == "__main__":
    unittest.main()
