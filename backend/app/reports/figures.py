"""Report figure generation using matplotlib for final presentation outputs."""
import os
from datetime import date

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def equity_curve_figure(equity_data: list[dict], benchmark_data: list[dict] | None = None,
                        output_path: str = "equity_curve.png") -> str:
    dates = [d["date"] for d in equity_data]
    values = [d["total_value"] for d in equity_data]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, values, label="Strategy", color="#4f8cff", linewidth=1.5)

    if benchmark_data:
        bm_values = [d.get("total_value", 0) for d in benchmark_data]
        ax.plot(dates[:len(bm_values)], bm_values, label="Benchmark (510050)",
                color="#8b8fa3", linewidth=1, linestyle="--")

    ax.set_title("Equity Curve", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def drawdown_figure(equity_data: list[dict], output_path: str = "drawdown.png") -> str:
    values = [d["total_value"] for d in equity_data]
    peak = values[0] if values else 0
    drawdowns = []
    for v in values:
        peak = max(peak, v)
        drawdowns.append((v - peak) / peak * 100)

    fig, ax = plt.subplots(figsize=(12, 4))
    dates = [d["date"] for d in equity_data]
    ax.fill_between(dates, drawdowns, 0, color="#f87171", alpha=0.3)
    ax.plot(dates, drawdowns, color="#f87171", linewidth=0.5)
    ax.set_title("Drawdown", fontsize=14, fontweight="bold")
    ax.set_ylabel("Drawdown (%)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def risk_state_timeline(states: list[dict], output_path: str = "risk_timeline.png") -> str:
    state_colors = {"NORMAL": "#34d399", "CAUTION": "#fbbf24",
                    "DEFENSIVE": "#f97316", "HALT": "#f87171"}
    dates = [s["date"] for s in states]
    state_vals = [{"NORMAL": 0, "CAUTION": 1, "DEFENSIVE": 2, "HALT": 3}[s["state"]]
                  for s in states]

    fig, ax = plt.subplots(figsize=(12, 3))
    for s_val, color in state_colors.items():
        mask = [v == {"NORMAL": 0, "CAUTION": 1, "DEFENSIVE": 2, "HALT": 3}[s_val]
                for v in state_vals]
        ax.scatter([dates[i] for i, m in enumerate(mask) if m],
                   [state_vals[i] for i, m in enumerate(mask) if m],
                   color=color, label=s_val, s=20)

    ax.set_yticks([0, 1, 2, 3])
    ax.set_yticklabels(["NORMAL", "CAUTION", "DEFENSIVE", "HALT"])
    ax.set_title("Risk State Timeline", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path
