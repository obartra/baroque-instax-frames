# SPDX-License-Identifier: MIT
"""Keep generated geometry separate from the distributed, validated projects."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P = Path(os.environ.get("BAROQUE_BUILD_DIR", ROOT / "build")).expanduser().resolve()
P.mkdir(parents=True, exist_ok=True)
(P / "validation").mkdir(exist_ok=True)
