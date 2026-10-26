import sys
import threading
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch

import tray
from test_video_output import arguments


class FakeIcon:
    """Enough of pystray.Icon to run the setup thread and click Quit."""

    def __init__(self, name, image, title, menu):
        self.menu = menu
        self.stopped = threading.Event()
        self.visible = False

    def run(self, setup):
        thread = threading.Thread(target=setup, args=(self,))
        thread.start()
        quit_item = next(item for item in self.menu if item.text == "Quit")
        quit_item.action(self, quit_item)
        self.stopped.wait(5)
        thread.join(5)

    def stop(self):
        self.stopped.set()


def fake_pystray():
    return SimpleNamespace(Icon=FakeIcon, Menu=lambda *items: items,
                           MenuItem=lambda text, action: SimpleNamespace(text=text, action=action))


class TrayTests(unittest.TestCase):
    def run_tray(self, camera):
        with ExitStack() as mocks:
            mocks.enter_context(patch.dict(sys.modules, pystray=fake_pystray()))
            mocks.enter_context(patch.object(tray, "run_camera", side_effect=camera))
            mocks.enter_context(patch.object(tray, "tray_icon_image", return_value=None))
            mocks.enter_context(patch.object(tray, "hide_dock_icon"))
            mocks.enter_context(patch.object(tray, "authorize_camera"))
            mocks.enter_context(patch("builtins.print"))
            return tray.run_tray(arguments(no_preview=True, tray=True))

    def test_quit_in_the_menu_stops_the_camera(self):
        seen = {}

        def camera(args, resources, controls):
            seen["stopped"] = controls.stop.wait(5)
            return 0

        self.assertEqual(self.run_tray(camera), 0)
        self.assertTrue(seen["stopped"])

    def test_camera_failure_takes_the_icon_down_and_surfaces_the_error(self):
        def camera(args, resources, controls):
            raise RuntimeError("camera gone")

        with self.assertRaisesRegex(RuntimeError, "camera gone"):
            self.run_tray(camera)


if __name__ == "__main__":
    unittest.main()
