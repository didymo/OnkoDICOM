# -*- mode: python ; coding: utf-8 -*-
# macOS (Apple silicon) app bundle. Build from the project environment:  uv run pyinstaller --noconfirm OnkoDICOM-Darwin.spec
# Built only with the latest Python OnkoDICOM supports (3.12): one installer, not one per Python version.
# Package data is found through PyInstaller's helpers, so no site-packages path is written here: whatever environment
# runs PyInstaller is the one bundled.
import hashlib
import os
import shutil
import tarfile
import tomllib
import urllib.request
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

with open('pyproject.toml', 'rb') as f:
    VERSION = tomllib.load(f)['project']['version']

# plastimatch, self-contained (Stuart's macOS port, #26): the asset of the v1.10.1-itk5 release on his GitLab, which is
# also its source (the GPL source offer). The same file and checksum as .gitea/workflows/ci.yml uses from Gitea.
# The app runs it from Contents/Frameworks/plastimatch/bin (src/Model/Plastimatch.executable), because an app opened
# from the Finder has no shell PATH. Its rpath is @executable_path/../lib, so bin/ and lib/ keep their layout.
# PLASTIMATCH_URL may name another copy; the SHA-256 is what is trusted.
PLASTIMATCH_URL = os.environ.get('PLASTIMATCH_URL') or (
    'https://gitlab.com/sjswerdloff/plastimatch/-/releases/v1.10.1-itk5/downloads/'
    'plastimatch-1.10.1-itk5-macos-arm64.tar.gz')
PLASTIMATCH_SHA256 = 'af8c29f239dc2fd297699719505bb593668aa250b2666de3b65eee9ad55e4f82'
PLASTIMATCH_TOP = 'plastimatch-1.10.1-itk5-macos-arm64'


def plastimatch_bundle():
    """Download (or reuse) the tarball, refuse it unless its SHA-256 matches, and unpack it fresh under build/."""
    work = Path('build', 'plastimatch')
    work.mkdir(parents=True, exist_ok=True)
    tgz = work / f'{PLASTIMATCH_SHA256}.tar.gz'
    if not tgz.is_file():
        part = work / 'download.part'
        urllib.request.urlretrieve(PLASTIMATCH_URL, part)
        part.replace(tgz)
    got = hashlib.sha256(tgz.read_bytes()).hexdigest()
    if got != PLASTIMATCH_SHA256:
        tgz.unlink()
        raise SystemExit(f'plastimatch tarball sha256 {got}, expected {PLASTIMATCH_SHA256}')
    unpacked = work / 'unpacked'
    shutil.rmtree(unpacked, ignore_errors=True)
    # The tarball was made by macOS tar, which stores extended attributes as AppleDouble "._name" entries. bsdtar folds
    # them back into attributes; tarfile would write them out as files, and codesign rejects them inside a bundle.
    def no_appledouble(member, path):
        if Path(member.name).name.startswith('._'):
            return None
        return tarfile.data_filter(member, path)

    with tarfile.open(tgz) as tar:
        tar.extractall(unpacked, filter=no_appledouble)
    top = unpacked / PLASTIMATCH_TOP
    if not (top / 'bin' / 'plastimatch').is_file():
        raise SystemExit(f'no bin/plastimatch in {tgz}')
    return str(top)


# Anonymisation writes real patient-name-and-ID-to-hash mappings to data/csv/patientHash.csv in the working directory,
# which in a developer's checkout is this repository's copy. So data/ is bundled file by file: that file is replaced by
# a header-only copy written here, and hidden entries (the test suite's data/.csv.* backups) are left out.
PATIENT_HASH = 'patientHash.csv'
PATIENT_HASH_HEADER = 'Pname and ID,Hashed_Pname\n'


def distributable_data():
    entries = []
    for path in sorted(Path('data').rglob('*')):
        rel = path.relative_to('data')
        if not path.is_file() or any(part.startswith('.') for part in rel.parts) or path.name == PATIENT_HASH:
            continue
        entries.append((str(path), str(Path('data') / rel.parent)))
    header_only = Path('build') / 'data-csv' / PATIENT_HASH
    header_only.parent.mkdir(parents=True, exist_ok=True)
    header_only.write_text(PATIENT_HASH_HEADER)
    entries.append((str(header_only), 'data/csv'))
    return entries


block_cipher = None

added_files = [
    ('res', 'res'),
    *distributable_data(),
    *collect_data_files('country_list'),
    *collect_data_files('pymedphys', includes=['_trf/decode/config.json']),
    *collect_data_files('pymedphys', include_py_files=True, includes=['_imports/imports.py']),
    # imblearn reads VERSION.txt on import.
    *collect_data_files('imblearn'),
    # pyradiomics validates its parameters against schemas/paramSchema.yaml, with schemaFuncs.py loaded by path.
    *collect_data_files('radiomics', include_py_files=True, subdir='schemas'),
    (plastimatch_bundle(), 'plastimatch'),
]

a = Analysis(['main.py'],
             pathex=[],
             binaries=collect_dynamic_libs("rtree"),
             datas=added_files,
             hiddenimports=['scipy.spatial.transform._rotation_groups'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='OnkoDICOM',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=False,
          target_arch='arm64')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='OnkoDICOM')
app = BUNDLE(coll,
             name='OnkoDICOM.app',
             icon='res/images/icon.icns',
             bundle_identifier='au.com.onkodicom',
             version=VERSION,
             info_plist={
                 'NSPrincipalClass': 'NSApplication',
                 'NSAppleScriptEnabled': False,
                 'NSHighResolutionCapable': True,
                 'LSMinimumSystemVersion': '15.0',
             },
)
