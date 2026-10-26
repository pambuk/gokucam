"""Run GokuCam from the system tray / menu bar: no preview window, the menu quits and recaptures the background."""

from __future__ import annotations

import argparse
import sys
from contextlib import ExitStack

import cv2

try:
    from .gokucam import Controls, run_camera
except ImportError:
    from gokucam import Controls, run_camera


def tray_icon_image(size: int = 64):
    """A four-star Dragon Ball drawn in code, like every other effect."""
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    unit = size / 64
    draw.ellipse((4 * unit, 4 * unit, 60 * unit, 60 * unit),
                 fill=(255, 150, 0), outline=(140, 60, 0), width=max(1, round(3 * unit)))
    for x, y in ((24, 24), (40, 24), (24, 40), (40, 40)):
        draw.ellipse(((x - 5) * unit, (y - 5) * unit, (x + 5) * unit, (y + 5) * unit), fill=(210, 30, 30))
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


def place_in_menu_bar(icon) -> None:
    """New macOS status items land at the left end of the status area, exactly where
    menu bar managers (Hidden Bar, Bartender, Ice) hide them. Ask for a spot near the
    right instead; macOS then remembers wherever the user drags it."""
    status_item = getattr(icon, "_status_item", None)  # pystray keeps it private, macOS only
    if status_item is None:
        return
    from Foundation import NSUserDefaults

    NSUserDefaults.standardUserDefaults().registerDefaults_(
        {"NSStatusItem Preferred Position GokuCam": 300.0})
    status_item.setAutosaveName_("GokuCam")


def authorize_camera(index: int) -> None:
    """macOS shows the camera permission prompt only from the main thread, and the
    camera loop runs in a worker, so touch the camera here first (no-op once granted)."""
    if sys.platform == "darwin":
        cv2.VideoCapture(index).release()


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
    place_in_menu_bar(icon)
    hide_dock_icon()
    authorize_camera(args.camera)
    print("[GokuCam] Running from the tray: its menu captures a new background or quits.")
    icon.run(setup=worker)
    if failure:
        raise failure[0]
    return 0
