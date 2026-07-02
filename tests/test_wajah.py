"""Unit test untuk modul wajah/ (display, faces, animator)."""

import unittest
from unittest.mock import MagicMock, patch

from config import DisplayConfig
from wajah import faces
from wajah.animator import Animator
from wajah.display import DisplayDriver


class TestFaces(unittest.TestCase):
    def test_face_happy_returns_correct_size_image(self):
        img = faces.face_happy(tick=0, blink=False)
        self.assertEqual(img.size, (240, 240))
        self.assertEqual(img.mode, "RGB")

    def test_all_mood_faces_return_image(self):
        self.assertEqual(faces.face_sad(0).size, (240, 240))
        self.assertEqual(faces.face_curious(0).size, (240, 240))
        self.assertEqual(faces.face_sleepy(0).size, (240, 240))
        self.assertEqual(faces.face_excited(0).size, (240, 240))
        self.assertEqual(faces.face_surprised(0).size, (240, 240))
        self.assertEqual(faces.face_bored(0).size, (240, 240))

    def test_face_talking_and_loading(self):
        talking = faces.face_talking(tick=5, intensity=0.8)
        loading = faces.face_loading()
        self.assertEqual(talking.size, (240, 240))
        self.assertEqual(loading.size, (240, 240))


class TestDisplayDriver(unittest.TestCase):
    def test_init_falls_back_to_simulation_without_hardware(self):
        """Tanpa modul ST7789/SPI hardware, driver harus degrade gracefully, bukan crash."""
        driver = DisplayDriver(DisplayConfig())
        driver.init()
        self.assertTrue(driver._simulated)

    def test_show_does_not_raise_in_simulation_mode(self):
        driver = DisplayDriver(DisplayConfig())
        driver.init()
        img = faces.face_idle(0)
        driver.show(img)  # tidak boleh melempar exception

    def test_brightness_clamped_between_0_and_100(self):
        driver = DisplayDriver(DisplayConfig())
        driver.init()
        driver.brightness(150)
        self.assertEqual(driver._backlight_level, 100)
        driver.brightness(-10)
        self.assertEqual(driver._backlight_level, 0)


class TestAnimator(unittest.TestCase):
    def setUp(self):
        self.display = MagicMock()
        self.display.config = DisplayConfig()
        self.mood_engine = MagicMock()
        self.mood_engine.mood = "happy"
        self.mood_engine.tick = 0

    def test_render_frame_uses_mood_engine_mood(self):
        anim = Animator(self.display, self.mood_engine)
        with patch("wajah.animator.faces.face_happy") as mock_face:
            mock_face.return_value = "fake_image"
            image = anim._render_frame()
            mock_face.assert_called_once()
            self.assertEqual(image, "fake_image")

    def test_set_talking_overrides_mood_rendering(self):
        anim = Animator(self.display, self.mood_engine)
        anim.set_talking(True, 0.5)
        with patch("wajah.animator.faces.face_talking") as mock_talk:
            mock_talk.return_value = "talking_image"
            image = anim._render_frame()
            mock_talk.assert_called_once_with(0, 0.5)
            self.assertEqual(image, "talking_image")

    def test_manual_mood_override(self):
        anim = Animator(self.display, self.mood_engine)
        anim.set_mood("sleepy")
        with patch("wajah.animator.faces.face_sleepy") as mock_face:
            mock_face.return_value = "sleepy_image"
            image = anim._render_frame()
            mock_face.assert_called_once()
            self.assertEqual(image, "sleepy_image")


if __name__ == "__main__":
    unittest.main()
