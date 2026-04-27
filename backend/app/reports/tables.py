"""Export performance metrics and trade summaries to CSV/Markdown."""
import csv
import io
from datetime import date


def metrics_to_csv(metrics: dict[str, float]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Metric", "Value"])
    for name, value in metrics.items():
        writer.writerow([name, f"{value:.4f}"])
    return output.getvalue()


def metrics_to_markdown(metrics: dict[str, float]) -> str:
    lines = ["| Metric | Value |", "|--------|-------|"]
    fmt_map = {
        "total_return": ".2%", "cagr": ".2%", "sharpe_ratio": ".2f",
        "max_drawdown": ".2%", "volatility": ".2%", "win_rate": ".2%",
    }
    for name, value in metrics.items():
        fmt = fmt_map.get(name, ".4f")
        try:
            lines.append(f"| {name} | {value:{fmt}} |")
        except (ValueError, TypeError):
            lines.append(f"| {name} | {value} |")
    return "\n".join(lines)


def trades_to_csv(trades: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Instrument", "Side", "Quantity", "Price", "Slippage", "Commission"])
    for t in trades:
        writer.writerow([t.get("date", ""), t.get("instrument_id", ""),
                         t.get("side", ""), t.get("quantity", 0),
                         t.get("price", 0), t.get("slippage", 0),
                         t.get("commission", 0)])
    return output.getvalue()
