"""Unit test untuk modul mulut/ (sounds, speaker, tts)."""

import unittest
from unittest.mock import MagicMock, patch

from config import AudioConfig
from mulut.sounds import SOUND_FILES, SoundManager
from mulut.speaker import Speaker
from mulut.tts import TextToSpeech
from nyawa.event_bus import EventBus


class TestSoundManager(unittest.TestCase):
    def setUp(self):
        self.config = AudioConfig(SOUNDS_DIR="/tmp/emorobot_test_sounds")
        self.manager = SoundManager(self.config)

    def test_all_required_sound_ids_present(self):
        required = {
            "startup", "happy", "sad", "curious", "excited",
            "sleepy", "touched", "surprised", "shutdown", "greeting",
        }
        self.assertEqual(required, set(SOUND_FILES.keys()))

    def test_path_for_unknown_id_raises_keyerror(self):
        with self.assertRaises(KeyError):
            self.manager.path_for("not_a_real_sound")

    def test_exists_false_when_file_missing(self):
        self.assertFalse(self.manager.exists("happy"))

    def test_missing_ids_lists_all_when_dir_empty(self):
        self.assertEqual(set(self.manager.missing_ids()), set(SOUND_FILES.keys()))


class TestSpeaker(unittest.TestCase):
    def test_init_degrades_gracefully_without_pygame(self):
        bus = EventBus()
        speaker = Speaker(bus, AudioConfig(SOUNDS_DIR="/tmp/emorobot_test_sounds"))
        with patch.dict("sys.modules", {"pygame": None}):
            speaker.init()
        self.assertFalse(speaker.is_playing)
        speaker.stop()

    def test_play_does_not_raise_when_file_missing(self):
        bus = EventBus()
        speaker = Speaker(bus, AudioConfig(SOUNDS_DIR="/tmp/emorobot_test_sounds"))
        speaker.init()
        speaker.play("happy")
        speaker.stop()

    def test_set_volume_clamped(self):
        bus = EventBus()
        speaker = Speaker(bus, AudioConfig())
        speaker.set_volume(2.0)
        self.assertEqual(speaker._config.VOLUME, 1.0)
        speaker.set_volume(-1.0)
        self.assertEqual(speaker._config.VOLUME, 0.0)


class TestTextToSpeech(unittest.TestCase):
    def test_speak_sync_emits_speaking_start_and_end(self):
        bus = MagicMock()
        tts = TextToSpeech(bus, AudioConfig())
        with patch("mulut.tts.subprocess.Popen") as mock_popen:
            mock_popen.return_value.wait.return_value = 0
            tts.speak_sync("halo")
        event_types = [call.args[0].type for call in bus.publish.call_args_list]
        self.assertEqual(event_types, ["SPEAKING_START", "SPEAKING_END"])

    def test_speak_sync_handles_missing_espeak_gracefully(self):
        bus = MagicMock()
        tts = TextToSpeech(bus, AudioConfig())
        with patch("mulut.tts.subprocess.Popen", side_effect=FileNotFoundError):
            tts.speak_sync("halo")  # tidak boleh raise
        event_types = [call.args[0].type for call in bus.publish.call_args_list]
        self.assertEqual(event_types, ["SPEAKING_START", "SPEAKING_END"])

    def test_stop_terminates_running_process(self):
        bus = MagicMock()
        tts = TextToSpeech(bus, AudioConfig())
        fake_process = MagicMock()
        tts._process = fake_process
        tts.stop()
        fake_process.terminate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
