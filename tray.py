"""Run GokuCam from the system tray / menu bar: no preview window, the menu quits and recaptures the background."""

from __future__ import annotations

import argparse
import sys
from contextlib import ExitStack

try:
    from .gokucam import Controls, run_camera
except ImportError:
    from gokucam import Controls, run_camera


def tray_icon_image():
    """A four-star Dragon Ball drawn in code, like every other effect."""
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 4, 60, 60), fill=(255, 150, 0), outline=(140, 60, 0), width=3)
    for x, y in ((24, 24), (40, 24), (24, 40), (40, 40)):
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(210, 30, 30))
    return image


def hide_dock_icon() -> None:
    """A tray app should not sit in the macOS Dock (same trick as LSUIElement)."""
    if sys.platform != "darwin":
        return
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
    except ImportError:
        return
    NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)


def run_tray(args: argparse.Namespace) -> int:
    try:
        import pystray
    except ImportError as error:
        raise RuntimeError("pystray is not installed. Run ./start.sh (or start.bat) to install it.") from error

    controls = Controls()
    failure: list[BaseException] = []

    # pystray owns the main thread (macOS insists), so the camera loop runs
    # in the setup thread and tears the icon down when it ends for any reason.
    def worker(icon) -> None:
        icon.visible = True
        try:
            with ExitStack() as resources:
                run_camera(args, resources, controls)
        except BaseException as error:  # noqa: BLE001 - re-raised in the main thread
            failure.append(error)
        finally:
            icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("New background", lambda icon, item: controls.recalibrate.set()),
        pystray.MenuItem("Quit", lambda icon, item: controls.stop.set()),
    )
    icon = pystray.Icon("gokucam", tray_icon_image(), "GokuCam", menu)
    hide_dock_icon()
    print("[GokuCam] Running from the tray: its menu captures a new background or quits.")
    icon.run(setup=worker)
    if failure:
        raise failure[0]
    return 0
