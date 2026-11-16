#!/bin/bash
# Fails when a macOS installer package VERSION-CHECKS the app (midst-editor issue 16, the 0.9.4 Tart run).
#
#     tools/check_pkg_not_version_checked.sh release/build/Midst-0.9.4-arm64.pkg [more.pkg ...]
#
# Why: pkgbuild marks an app bundle version-checked unless told otherwise. A version-checked bundle is
# not written when the Mac already has a newer copy of it. The preinstall keeps any Midst already in
# Applications by renaming it aside, so the installer is left writing nothing at all: the poet is left
# with no "Midst" in Applications, and the installer still says "The installation was successful".
# The 0.9.4 package did exactly that over a Midst 99.0.0 (check_installed_package.sh step 3c).
# This checks the built package, because that is what a poet runs.
#
# How: a version-checked package lists its bundle inside <bundle-version> in PackageInfo; one that is
# not has an empty <bundle-version/>.
#
# CONTROL, every run: two throwaway packages are built here, one version-checked and one not, and the
# detector must tell them apart. If it cannot, the result means nothing and the exit status is 2.
#
# Exit 0: no package version-checks. 1: at least one does. 2: the check could not run. macOS only.
set -euo pipefail
[ $# -ge 1 ] || { echo "usage: $0 <installer.pkg> [more.pkg ...]" >&2; exit 2; }
for tool in pkgbuild pkgutil plutil; do
  command -v "$tool" > /dev/null || { echo "$0: $tool not found (this check runs on macOS)" >&2; exit 2; }
done

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# Prints the number of PackageInfo files in the package that version-check a bundle. A product archive
# (what electron-builder makes) holds one component package per directory; a component package holds
# PackageInfo at its top. Both are covered by searching the expanded tree.
version_checking() {
  local out="$work/expanded.$RANDOM$RANDOM"
  pkgutil --expand "$1" "$out" > /dev/null || { echo "$0: could not expand $1" >&2; return 2; }
  local infos
  infos=$(find "$out" -name PackageInfo -type f)
  [ -n "$infos" ] || { echo "$0: no PackageInfo inside $1" >&2; return 2; }
  local n=0 info
  while IFS= read -r info; do
    # A bundle listed between <bundle-version> and </bundle-version>. An empty <bundle-version/> has
    # no closing tag.
    if awk '/<bundle-version>/ { inside = 1 } inside && /<bundle / { found = 1 } /<\/bundle-version>/ { inside = 0 }
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
<key>CFBundleIdentifier</key><string>invalid.example.version-check-control</string>
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
for checked in true false; do
  cp "$work/component.plist" "$work/component_$checked.plist"
  plutil -replace 0.BundleIsVersionChecked -bool "$checked" "$work/component_$checked.plist"
  pkgbuild --root "$work/root" --identifier invalid.example.version-check-control \
    --component-plist "$work/component_$checked.plist" --install-location /Applications \
    "$work/control_$checked.pkg" > /dev/null
done
seen_true=$(version_checking "$work/control_true.pkg")
seen_false=$(version_checking "$work/control_false.pkg")
if [ "$seen_true" != 1 ] || [ "$seen_false" != 0 ]; then
  echo "$0: CONTROL FAILED. A version-checked control package read as $seen_true and an unchecked one" \
    "as $seen_false (expected 1 and 0), so nothing can be concluded about the real package." >&2
  exit 2
fi

status=0
for pkg in "$@"; do
  [ -f "$pkg" ] || { echo "$0: no such file: $pkg" >&2; exit 2; }
  n=$(version_checking "$pkg")
  if [ "$n" = 0 ]; then
    echo "$(basename "$pkg"): not version-checked; it writes the app over any version (control holds)"
  else
    echo "$(basename "$pkg"): VERSION-CHECKED. Over a newer Midst, the preinstall keeps the newer one and" \
      "the installer then writes nothing, so Applications is left with no Midst. Set build.pkg.isVersionChecked to false." >&2
    status=1
  fi
done
exit "$status"
