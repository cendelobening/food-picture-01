"""food-picture-01 entry runner.

Delivers the bundled food picture (entry.png, sitting next to this file)
to the output directory as entry.png.

The picture is the whole entry: a lacquered roast duck, sliced open,
steaming on a dark platter. This script does not draw anything at run
time -- it ships the exact bytes that were judged, so every run produces
the identical file.

Before copying, it inspects the picture's own header and refuses to ship
it unless it is a PNG or a JPEG within the competition limits (at most
1 MiB, at most 1024 px on a side). The copy goes through a scratch file
that is moved into place, so a failed run never leaves a half-written
image behind, and the finished copy is checked by size and SHA-256.
The delivered file is made world-readable (mode 0644): the grader
collects the output as a different user than the one running this
program, so an owner-only file would be unreadable to it.

Usage: python3 main.py
Output: $MAKEFUN_OUTPUT_DIR/entry.png (falls back to /output/entry.png)
"""

import hashlib
import os
import struct
import sys
import tempfile
from pathlib import Path

SOURCE_NAME = "entry.png"
MAX_BYTES = 1_048_576
MAX_DIMENSION = 1024


def sha256_of(path):
    """SHA-256 hex digest of a file, read in 1 MiB chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def image_size(path):
    """Return (format, width, height) for a PNG or JPEG, from its header.

    Only the header is parsed: the PNG IHDR dimensions, or the first
    JPEG start-of-frame segment that carries dimensions.
    """
    data = path.read_bytes()
    if len(data) < 24:
        raise ValueError("image file too small to hold a header")
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        width, height = struct.unpack(">II", data[16:24])
        return "PNG", width, height
    if data[:2] == b"\xff\xd8":
        pos = 2
        while pos + 9 < len(data):
            if data[pos] != 0xFF:
                raise ValueError("corrupt JPEG marker stream")
            marker = data[pos + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
                return "JPEG", width, height
            if marker == 0xD9:
                break
            length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
            pos += 2 + length
        raise ValueError("no JPEG frame header found")
    raise ValueError("image is neither PNG nor JPEG")


def image_is_whole(path, fmt):
    """True if the file holds a complete image, not a truncated one.

    A PNG must end with its IEND chunk; a JPEG must end with the
    end-of-image marker. Anything shorter is a partial download.
    """
    data = path.read_bytes()
    if fmt == "PNG":
        return data.rstrip(b"\x00")[-12:] == b"\x00\x00\x00\x00IEND\xaeB`\x82"
    return data.rstrip(b"\x00")[-2:] == b"\xff\xd9"


def main():
    here = Path(__file__).resolve().parent
    source = here / SOURCE_NAME
    if not source.is_file():
        print(f"missing {SOURCE_NAME} next to main.py", file=sys.stderr)
        return 1

    size = source.stat().st_size
    if size > MAX_BYTES:
        print(f"{SOURCE_NAME} is {size} bytes, over the 1 MiB limit",
              file=sys.stderr)
        return 1
    fmt, width, height = image_size(source)
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        print(f"{fmt} is {width}x{height}, over the 1024 px limit",
              file=sys.stderr)
        return 1
    if not image_is_whole(source, fmt):
        print(f"{fmt} file looks truncated (missing end marker)",
              file=sys.stderr)
        return 1

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / SOURCE_NAME

    expected_hash = sha256_of(source)
    with tempfile.NamedTemporaryFile(dir=out_dir, delete=False,
                                     prefix=".entry-", suffix=".tmp") as tmp:
        tmp_path = Path(tmp.name)
        with source.open("rb") as src:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)
    # NamedTemporaryFile creates the scratch file mode 0600, and
    # os.replace keeps that mode on the delivered file. The grader
    # collects /output as a different user than the one running this
    # program, so an owner-only file is unreadable to it ("entry.png
    # is not readable"). Make the copy world-readable before it is
    # moved into place.
    os.chmod(tmp_path, 0o644)
    try:
        os.replace(tmp_path, target)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
    # Belt and braces: the delivered file must stay world-readable
    # even if the move above ever preserves a different mode.
    os.chmod(target, 0o644)

    actual_size = target.stat().st_size
    actual_hash = sha256_of(target)
    if actual_size != size or actual_hash != expected_hash:
        print("output verification failed: copy does not match source",
              file=sys.stderr)
        return 1

    print(f"wrote {target} ({fmt} {width}x{height}, {size} bytes, "
          f"sha256 {actual_hash})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
