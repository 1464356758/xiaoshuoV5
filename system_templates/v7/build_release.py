"""Build the reproducible, self-contained A7 initializer from the versioned source."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from novel import EDITION, PACKAGE_FILES, SCHEMA, VERSION

ROOT = Path(__file__).resolve().parent


def build(output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    files = {p: (ROOT / p).read_bytes() for p in sorted(PACKAGE_FILES)}
    manifest = {"engine": SCHEMA, "edition": EDITION, "version": VERSION,
                "files": {p: hashlib.sha256(raw).hexdigest() for p, raw in files.items()}}
    files["INIT_MANIFEST.json"] = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026,11,18,0,0,0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return {"version": VERSION, "files":len(files), "bytes":output.stat().st_size,
            "sha256":hashlib.sha256(output.read_bytes()).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(build(args.output), ensure_ascii=False))
