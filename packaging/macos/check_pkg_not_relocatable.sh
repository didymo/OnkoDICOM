#!/bin/bash
# Fails when a macOS installer package would RELOCATE the app (midst-editor issue 57).
#
#     tools/check_pkg_not_relocatable.sh release/build/Midst-0.2.0-arm64.pkg [more.pkg ...]
#
# Why: pkgbuild marks an app bundle relocatable unless told otherwise. A relocatable package does
# not install to /Applications when macOS already knows a copy of the app (same bundle identifier)
# anywhere else: it updates that copy where it lies, in ~/Applications, in Downloads, even in the
# Trash. The installer still says "The installation was successful", and nothing appears in
# Applications. package.json build.pkg.isRelocatable turns it off; this checks the built package,
# because that is what a poet runs.
#
# How: a relocatable package lists its bundle inside <relocate> in PackageInfo; a fixed one has an
# empty <relocate/>. (The relocatable="..." attribute on <pkg-info> is NOT the signal: it reads
# "false" in both.)
#
# CONTROL, every run: two throwaway packages are built here, one relocatable and one not, and the
# detector must tell them apart. If it cannot, the result means nothing and the exit status is 2.
#
# Exit 0: no package relocates. 1: at least one does. 2: the check could not run. macOS only.
set -euo pipefail
[ $# -ge 1 ] || { echo "usage: $0 <installer.pkg> [more.pkg ...]" >&2; exit 2; }
for tool in pkgbuild pkgutil plutil; do
  command -v "$tool" > /dev/null || { echo "$0: $tool not found (this check runs on macOS)" >&2; exit 2; }
done

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# Prints the number of PackageInfo files in the package that relocate a bundle. A product archive
# (what electron-builder makes) holds one component package per directory; a component package
# holds PackageInfo at its top. Both are covered by searching the expanded tree.
relocating() {
  local out="$work/expanded.$RANDOM$RANDOM"
  pkgutil --expand "$1" "$out" > /dev/null || { echo "$0: could not expand $1" >&2; return 2; }
  local infos
  infos=$(find "$out" -name PackageInfo -type f)
  [ -n "$infos" ] || { echo "$0: no PackageInfo inside $1" >&2; return 2; }
  local n=0 info
  while IFS= read -r info; do
    # A bundle listed between <relocate> and </relocate>. An empty <relocate/> has no closing tag.
    if awk '/<relocate>/ { inside = 1 } inside && /<bundle / { found = 1 } /<\/relocate>/ { inside = 0 }
            END { exit found ? 0 : 1 }' "$info"; then
      n=$((n + 1))
    fi
  done <<< "$infos"
  echo "$n"
}

# The control: the same empty app, packaged both ways.
app="$work/root/Control.app/Contents"
mkdir -p "$app/MacOS"
cat > "$app/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>invalid.example.relocation-control</string>
<key>CFBundleName</key><string>Control</string>
<key>CFBundleExecutable</key><string>Control</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>0.0.1</string>
<key>CFBundleVersion</key><string>0.0.1</string>
</dict></plist>
PLIST
printf '#!/bin/sh\n' > "$app/MacOS/Control"
chmod +x "$app/MacOS/Control"
pkgbuild --analyze --root "$work/root" "$work/component.plist" > /dev/null
for relocatable in true false; do
  cp "$work/component.plist" "$work/component_$relocatable.plist"
  plutil -replace 0.BundleIsRelocatable -bool "$relocatable" "$work/component_$relocatable.plist"
  pkgbuild --root "$work/root" --identifier invalid.example.relocation-control \
    --component-plist "$work/component_$relocatable.plist" --install-location /Applications \
    "$work/control_$relocatable.pkg" > /dev/null
done
seen_true=$(relocating "$work/control_true.pkg")
seen_false=$(relocating "$work/control_false.pkg")
if [ "$seen_true" != 1 ] || [ "$seen_false" != 0 ]; then
  echo "$0: CONTROL FAILED. A relocatable control package read as $seen_true and a fixed one as" \
    "$seen_false (expected 1 and 0), so nothing can be concluded about the real package." >&2
  exit 2
fi

status=0
for pkg in "$@"; do
  [ -f "$pkg" ] || { echo "$0: no such file: $pkg" >&2; exit 2; }
  n=$(relocating "$pkg")
  if [ "$n" = 0 ]; then
    echo "$(basename "$pkg"): not relocatable; it installs where the installer says (control holds)"
  else
    echo "$(basename "$pkg"): RELOCATABLE. If any other copy of the app exists on the Mac, the installer" \
      "updates that copy and puts nothing in Applications. Set build.pkg.isRelocatable to false." >&2
    status=1
  fi
done
exit "$status"
