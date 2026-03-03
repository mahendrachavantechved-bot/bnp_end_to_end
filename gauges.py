# gauges.py
"""
Gauge chart generators for DSCR and LTV.
Returns base64-encoded PNG strings for ft.Image(src_base64=...).

matplotlib is available in the Flet web (Pyodide) build via pyproject.toml.
Both functions are wrapped in try/except so the app never crashes if
matplotlib is unavailable in a stripped build.
"""

import io
import base64


def _b64(fig) -> str:
    """Render a matplotlib figure to base64 PNG and close it."""
    import matplotlib.pyplot as plt
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight",
                transparent=True, dpi=96)
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode("utf-8")


def dscr_gauge(dscr: float) -> str:
    """
    Render a DSCR speedometer gauge.
      Green  : DSCR 0 – 1.25  (marginal)
      Orange : DSCR 1.25 – 2.0 (acceptable)
      Red    : DSCR > 2.0       (strong)
    Returns base64 PNG string.
    """
    try:
        import numpy as np
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(5, 3), subplot_kw={"polar": True})
        fig.patch.set_facecolor("#0d1117")
        ax.set_facecolor("#0d1117")
        ax.set_theta_offset(1.5708)
        ax.set_theta_direction(-1)

        # Background arc
        ax.barh(0, 2 * np.pi, height=0.6, color="#30363d", alpha=0.6)

        # Colour bands
        green_end  = min(dscr, 1.25) / 3.0 * 2 * np.pi
        orange_end = min(dscr, 2.0)  / 3.0 * 2 * np.pi
        ax.barh(0, green_end,               height=0.6, color="#3fb950", alpha=0.9)
        ax.barh(0, orange_end - green_end,  left=green_end,
                height=0.6, color="#e3b341", alpha=0.9)
        ax.barh(0, 2 * np.pi - orange_end, left=orange_end,
                height=0.6, color="#f85149", alpha=0.8)

        # Needle
        needle_angle = min(dscr / 3.0, 1.0) * 2 * np.pi
        ax.plot([0, needle_angle], [0, 0.9], color="white", lw=4, solid_capstyle="round")
        ax.plot(0, 0, marker="o", ms=14, color="white")

        ax.set_ylim(0, 1)
        ax.axis("off")

        # Label
        ax.text(0, -0.5, f"DSCR  {dscr:.2f}",
                ha="center", va="center", fontsize=18, fontweight="bold",
                color="white", transform=ax.transData)

        return _b64(fig)

    except Exception:
        return ""


def ltv_gauge(ltv: float) -> str:
    """
    Render an LTV speedometer gauge (0 – 100 %).
      Green  : LTV ≤ 65 %
      Orange : LTV 65 – 80 %
      Red    : LTV > 80 %
    Returns base64 PNG string.
    """
    try:
        import numpy as np
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(5, 3), subplot_kw={"polar": True})
        fig.patch.set_facecolor("#0d1117")
        ax.set_facecolor("#0d1117")
        ax.set_theta_offset(1.5708)
        ax.set_theta_direction(-1)

        ax.barh(0, 2 * np.pi, height=0.6, color="#30363d", alpha=0.6)

        green_end  = min(ltv, 65) / 100 * 2 * np.pi
        orange_end = min(ltv, 80) / 100 * 2 * np.pi
        ax.barh(0, green_end,               height=0.6, color="#3fb950", alpha=0.9)
        ax.barh(0, orange_end - green_end,  left=green_end,
                height=0.6, color="#e3b341", alpha=0.9)
        ax.barh(0, 2 * np.pi - orange_end, left=orange_end,
                height=0.6, color="#f85149", alpha=0.8)

        needle_angle = (ltv / 100) * 2 * np.pi
        ax.plot([0, needle_angle], [0, 0.9], color="white", lw=4, solid_capstyle="round")
        ax.plot(0, 0, marker="o", ms=14, color="white")

        ax.set_ylim(0, 1)
        ax.axis("off")

        ax.text(0, -0.5, f"LTV  {ltv:.1f}%",
                ha="center", va="center", fontsize=18, fontweight="bold",
                color="white", transform=ax.transData)

        return _b64(fig)

    except Exception:
        return ""
