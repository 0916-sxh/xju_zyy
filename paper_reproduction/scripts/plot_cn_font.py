"""Shared Chinese matplotlib font helper."""

from __future__ import annotations

import os
from functools import lru_cache

import matplotlib.pyplot as plt


@lru_cache(maxsize=1)
def chinese_fontproperties():
    import matplotlib.font_manager as fm

    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                return fm.FontProperties(fname=path)
            except Exception:
                continue
    return None


def setup_chinese_style() -> None:
    import matplotlib.font_manager as fm

    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                fm.fontManager.addfont(path)
            except Exception:
                pass

    fp = chinese_fontproperties()
    if fp is not None:
        name = fp.get_name()
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def apply_cn_to_figure(fig, fp) -> None:
    """Re-apply CJK font after tight_layout (which may reset tick label fonts)."""
    if fp is None:
        return
    for ax in fig.axes:
        ax.set_title(ax.get_title(), fontproperties=fp)
        ax.set_xlabel(ax.get_xlabel(), fontproperties=fp)
        ax.set_ylabel(ax.get_ylabel(), fontproperties=fp)
        for lbl in ax.get_xticklabels() + ax.get_yticklabels():
            lbl.set_fontproperties(fp)
    for text in fig.texts:
        text.set_fontproperties(fp)


def cn(text: str) -> str:
    """Return text; use with fontproperties=chinese_fontproperties()."""
    return text
