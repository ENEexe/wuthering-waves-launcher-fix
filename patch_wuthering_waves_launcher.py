#!/usr/bin/env python3
"""Patch Wuthering Waves' WebView2 transparency flag in launcher_main.dll."""
from pathlib import Path
import os
import shutil
import stat
import sys
import tempfile

if len(sys.argv) != 2:
    raise SystemExit(f"Usage: python3 {Path(sys.argv[0]).name} /path/to/launcher_main.dll")

dll = Path(sys.argv[1]).expanduser()
if not dll.is_file() or dll.is_symlink():
    raise SystemExit(f"Not a regular launcher_main.dll file: {dll}")

old = b"\x12AllowsTransparency"
replacement = b"\x09IsEnabled\x1bA\x00\x03AAAAA"
original = dll.read_bytes()
count = original.count(old)
if count == 0:
    if original.count(replacement):
        print("This DLL is already patched; no change made.")
        raise SystemExit(0)
    raise SystemExit("Expected AllowsTransparency marker not found; no change made. Check that this is the current launcher DLL.")
if replacement in original:
    raise SystemExit("Both original and replacement markers are present; refusing a partial/ambiguous patch.")
if len(old) != len(replacement):
    raise SystemExit("Replacement length mismatch; no change made.")

backup = Path(str(dll) + ".bak")
suffix = 1
while backup.exists():
    backup = Path(f"{dll}.bak.{suffix}")
    suffix += 1
shutil.copy2(dll, backup)

patched = original.replace(old, replacement)
fd, temp_name = tempfile.mkstemp(prefix=f".{dll.name}.", suffix=".tmp", dir=dll.parent)
try:
    with os.fdopen(fd, "wb") as stream:
        stream.write(patched)
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(temp_name, stat.S_IMODE(dll.stat().st_mode))
    os.replace(temp_name, dll)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)

readback = dll.read_bytes()
if (len(readback) != len(original) or readback.count(old) != 0
        or readback.count(replacement) != count or backup.read_bytes() != original):
    shutil.copy2(backup, dll)
    raise SystemExit("Verification failed; the original DLL was restored from the backup.")

print(f"Patched {count} transparency marker(s): {dll}")
print(f"Verified original backup: {backup}")
print("Verified DLL size unchanged and all markers replaced.")
