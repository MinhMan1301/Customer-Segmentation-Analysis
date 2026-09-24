"""Package the large CSV files for a GitHub Release and write their checksums.

Creates reproducible ``.csv.gz`` files (fixed gzip mtime, so the same input
always gives the same checksum) in ``dist/dataset/`` and writes
``src/data/dataset.sha256`` in ``sha256sum -c`` format. Commit the manifest,
upload the ``.gz`` files to the ``dataset-v1`` release; the Jenkins Release
stage downloads them and refuses any file whose checksum does not match.

Usage:  python scripts/package_dataset.py
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LARGE_FILES = ("transactions_data_25pc.csv", "train_fraud_labels.csv")


def sha256_of(path: Path, block_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(block_size), b""):
            digest.update(block)
    return digest.hexdigest()


def gzip_file(source: Path, target: Path) -> Path:
    with source.open("rb") as raw, target.open("wb") as out:
        with gzip.GzipFile(filename=source.name, mode="wb", fileobj=out, mtime=0, compresslevel=9) as gz:
            shutil.copyfileobj(raw, gz, 1 << 20)
    return target


def package(source_dir: Path, dist_dir: Path, manifest: Path, files=LARGE_FILES) -> list[str]:
    dist_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    for name in files:
        csv_path = source_dir / name
        gz_path = gzip_file(csv_path, dist_dir / f"{name}.gz")
        lines.append(f"{sha256_of(gz_path)}  {gz_path.name}")
        lines.append(f"{sha256_of(csv_path)}  {name}")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return lines


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=ROOT / "src" / "data")
    parser.add_argument("--dist", type=Path, default=ROOT / "dist" / "dataset")
    parser.add_argument("--manifest", type=Path, default=ROOT / "src" / "data" / "dataset.sha256")
    args = parser.parse_args(argv)
    for line in package(args.source, args.dist, args.manifest):
        print(line)
    print(f"Upload {args.dist}/*.gz to the GitHub Release and commit {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
