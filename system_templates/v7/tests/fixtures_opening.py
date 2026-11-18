"""Read the two original scenes shipped in the guide; generate length-controlled test data separately."""
from pathlib import Path
import random


guide = (Path(__file__).resolve().parents[1] / "读稿示范.md").read_text(encoding="utf-8")
AT_THE_STAGE = guide.split("### 翻谱子的开法\n", 1)[1].split("### 敲碗的开法", 1)[0].strip()
AT_THE_TABLE = guide.split("### 敲碗的开法\n", 1)[1].split("### 读到末行再判断", 1)[0].strip()


def transport_text(chapter, size):
    # Entropy and length are controlled in transport tests; this is explicitly not fiction.
    rng = random.Random(1719 + chapter * 10000 + size)
    return ''.join(chr(rng.randrange(0x4e00, 0x8000)) for _ in range(size))
