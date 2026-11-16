#!/usr/bin/env bash
# Build the OnkoDICOM installer: a .pkg that puts OnkoDICOM.app in /Applications (#93).
#
#   packaging/macos/build_pkg.sh APP OUT.pkg [INSTALLER_IDENTITY [KEYCHAIN]]
#
# Without INSTALLER_IDENTITY the .pkg is unsigned (a local check). The app must already be signed (sign_app.sh).
# pkgbuild's defaults are turned off, as in Midst (#57, #16): a relocatable bundle lets the installer update a copy of
# the app found anywhere on the Mac and put nothing in /Applications, and a version-checked bundle writes nothing over a
# newer copy. Both report success. The built package is read back to check both are off.
set -euo pipefail

die() { echo "build_pkg.sh: $*" >&2; exit 1; }
[ $# -ge 2 ] || die "usage: build_pkg.sh APP OUT.pkg [INSTALLER_IDENTITY [KEYCHAIN]]"
app=$1
out=$2
identity=${3:-}
keychain=${4:-}
[ -d "$app/Contents/MacOS" ] || die "$app is not an app bundle"
codesign --verify --deep --strict "$app" || die "$app is not validly signed; run sign_app.sh first"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir "$work/root"
ditto "$app" "$work/root/$(basename "$app")"

pkgbuild --analyze --root "$work/root" "$work/component.plist" > /dev/null
/usr/libexec/PlistBuddy -c 'Set :0:BundleIsRelocatable false' -c 'Set :0:BundleIsVersionChecked false' \
  "$work/component.plist"

version=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$app/Contents/Info.plist")
id=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$app/Contents/Info.plist")
pkgbuild --root "$work/root" --component-plist "$work/component.plist" --install-location /Applications \
  --identifier "$id" --version "$version" "$work/component.pkg" > /dev/null

sign=()
if [ -n "$identity" ]; then
  sign=(--sign "$identity" --timestamp)
  [ -z "$keychain" ] || sign+=(--keychain "$keychain")
fi
productbuild --package "$work/component.pkg" ${sign[@]+"${sign[@]}"} "$out" > /dev/null

# Read the package back. The two checks are Midst's (midst-editor/tools), each with its own positive control.
here=$(cd "$(dirname "$0")" && pwd)
pkgutil --expand "$out" "$work/expanded"
info=$(find "$work/expanded" -name PackageInfo | sed -n 1p)
[ -n "$info" ] || die "no PackageInfo in $out"
grep -q 'install-location="/Applications"' "$info" || die "$out does not install to /Applications"
"$here/check_pkg_not_relocatable.sh" "$out"
"$here/check_pkg_not_version_checked.sh" "$out"
echo "built $out (OnkoDICOM $version, $id)${identity:+, signed by $identity}"
