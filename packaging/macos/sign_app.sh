#!/usr/bin/env bash
# Sign OnkoDICOM.app inside-out with the hardened runtime (#93), then verify it.
#
#   packaging/macos/sign_app.sh APP IDENTITY [KEYCHAIN]
#
# IDENTITY is a "Developer ID Application: ..." name or SHA-1, or "-" for an ad hoc signature (a local check of the
# hardened runtime; it cannot be notarized). Every Mach-O file is signed, deepest first, then each .framework, then the
# app with packaging/macos/entitlements.plist. Nested code gets no entitlements: they only take effect on the main
# executable. Symlinks are skipped (their targets are signed). Exit 0 only if codesign --verify --deep --strict passes.
set -euo pipefail

die() { echo "sign_app.sh: $*" >&2; exit 1; }
[ $# -ge 2 ] || die "usage: sign_app.sh APP IDENTITY [KEYCHAIN]"
app=$1
identity=$2
keychain=${3:-}
here=$(cd "$(dirname "$0")" && pwd)
entitlements="$here/entitlements.plist"
[ -d "$app/Contents/MacOS" ] || die "$app is not an app bundle"
[ -f "$entitlements" ] || die "no $entitlements"

args=(--force --options runtime --sign "$identity")
[ "$identity" = - ] || args+=(--timestamp)
[ -z "$keychain" ] || args+=(--keychain "$keychain")

machos=$(mktemp)
adhoc_entitlements=$(mktemp)
trap 'rm -f "$machos" "$adhoc_entitlements"' EXIT
# An ad hoc signature has no Team ID, and the hardened runtime's library validation refuses every library whose Team ID
# differs from the process's, so an ad hoc build cannot load libpython. For the local check only, library validation is
# turned off. A Developer ID build signs every file with one Team ID and never gets this entitlement.
if [ "$identity" = - ]; then
  cp "$entitlements" "$adhoc_entitlements"
  /usr/libexec/PlistBuddy -c 'Add :com.apple.security.cs.disable-library-validation bool true' "$adhoc_entitlements"
  entitlements=$adhoc_entitlements
fi

main="$app/Contents/MacOS/$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$app/Contents/Info.plist")"

# Mach-O files, by content rather than name (plastimatch's binary has no extension), excluding the main executable,
# deepest path first so nothing is signed before what it contains.
while IFS= read -r -d '' f; do
  [ "$f" = "$main" ] && continue
  case "$(file -b "$f")" in
    Mach-O*) printf '%s\n' "$f" ;;
  esac
done < <(find "$app/Contents" -type f -print0) | awk -F/ '{ print NF "\t" $0 }' | sort -rn | cut -f2- > "$machos"

count=$(wc -l < "$machos" | tr -d ' ')
[ "$count" -gt 0 ] || die "no Mach-O files found in $app"
echo "signing $count Mach-O files"
while IFS= read -r f; do
  codesign "${args[@]}" "$f" || die "codesign failed on $f"
done < "$machos"

while IFS= read -r -d '' fw; do
  codesign "${args[@]}" "$fw" || die "codesign failed on $fw"
done < <(find "$app/Contents" -name '*.framework' -type d -print0)

codesign "${args[@]}" --entitlements "$entitlements" "$app" || die "codesign failed on $app"

codesign --verify --deep --strict --verbose=2 "$app" || die "verification failed for $app"
echo "signed and verified: $app ($identity)"
