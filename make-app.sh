#!/usr/bin/env bash
# Build GokuCam.app (macOS): a double-clickable tray app that runs ./start.sh --tray
# from this folder. Run ./start.sh once from the terminal first so the .venv exists.
set -euo pipefail
cd "$(dirname "$0")"
REPO="$PWD"
APP="$REPO/GokuCam.app"
VENV_PY="$REPO/.venv/bin/python"

[ -x "$VENV_PY" ] || { echo "[GokuCam] Run ./start.sh once first to create .venv" >&2; exit 1; }

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>GokuCam</string>
  <key>CFBundleDisplayName</key><string>GokuCam</string>
  <key>CFBundleIdentifier</key><string>io.github.gokucam.tray</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>GokuCam</string>
  <key>CFBundleIconFile</key><string>GokuCam</string>
  <key>LSUIElement</key><true/>
  <key>NSCameraUsageDescription</key><string>GokuCam draws the effects on your webcam.</string>
</dict>
</plist>
PLIST

# The repo path is baked in, so the app keeps working if it is moved to /Applications.
cat > "$APP/Contents/MacOS/GokuCam" <<LAUNCHER
#!/usr/bin/env bash
cd "$REPO"
exec env PYTHONUNBUFFERED=1 ./start.sh --tray "\$@" >> "\$HOME/Library/Logs/GokuCam.log" 2>&1
LAUNCHER
chmod +x "$APP/Contents/MacOS/GokuCam"

# App icon: the same Dragon Ball as the tray icon, rendered at the sizes iconutil wants.
ICONSET="$(mktemp -d)/GokuCam.iconset"
mkdir -p "$ICONSET"
"$VENV_PY" -c "
from tray import tray_icon_image
for size in (16, 32, 128, 256, 512):
    tray_icon_image(size).save(f'$ICONSET/icon_{size}x{size}.png')
    tray_icon_image(size * 2).save(f'$ICONSET/icon_{size}x{size}@2x.png')
"
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/GokuCam.icns"
rm -rf "$(dirname "$ICONSET")"

echo "[GokuCam] Built $APP. Double-click it, or drag it to /Applications."
echo "[GokuCam] Output goes to ~/Library/Logs/GokuCam.log"
