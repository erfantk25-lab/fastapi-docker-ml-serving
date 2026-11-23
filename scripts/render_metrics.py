"""Render a compact SVG dashboard from the metrics of the latest model run.

Usage: uv run python scripts/render_metrics.py
Reads outputs/metrics.json and writes docs/model_metrics.svg.
"""
from __future__ import annotations

import json
from pathlib import Path

METRICS = Path("outputs/metrics.json")
OUTPUT = Path("docs/model_metrics.svg")


def main() -> None:
    if not METRICS.is_file():
        raise SystemExit("outputs/metrics.json not found. Train the model first.")

    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    required = ("roc_auc", "accuracy")
    missing = [key for key in required if key not in metrics]
    if missing:
        raise SystemExit(f"Missing required metrics: {', '.join(missing)}")

    cards = [
        ("ROC AUC", float(metrics["roc_auc"]), "ranking · held-out test split"),
        ("Accuracy", float(metrics["accuracy"]), "classification · held-out test split"),
    ]
    for threshold in (0.3, 0.4, 0.5, 0.6, 0.7):
        prefix = f"threshold_{threshold:.1f}"
        if all(f"{prefix}_{name}" in metrics for name in ("precision", "recall", "f1")):
            cards.extend([
                (f"Precision · {threshold:.1f}", float(metrics[f"{prefix}_precision"]), "threshold-specific"),
                (f"Recall · {threshold:.1f}", float(metrics[f"{prefix}_recall"]), "threshold-specific"),
                (f"F1 · {threshold:.1f}", float(metrics[f"{prefix}_f1"]), "threshold-specific"),
            ])

    width, card_w, card_h, gap = 1000, 300, 132, 18
    cols = 3
    rows = (len(cards) + cols - 1) // cols
    height = 100 + rows * (card_h + gap)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" rx="24" fill="#071426"/>',
        '<text x="36" y="48" fill="#42d9f5" font-family="Arial,sans-serif" font-size="15" font-weight="700" letter-spacing="2">MODEL EVALUATION · LATEST TRAINING RUN</text>',
    ]
    for index, (label, value, note) in enumerate(cards):
        col, row = index % cols, index // cols
        x, y = 36 + col * (card_w + gap), 72 + row * (card_h + gap)
        bar_width = max(0, min(1, value)) * (card_w - 44)
        parts.extend([
            f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="16" fill="#102b49" stroke="#29445e"/>',
            f'<text x="{x + 20}" y="{y + 30}" fill="#b9ccdc" font-family="Arial,sans-serif" font-size="14">{label}</text>',
            f'<text x="{x + 20}" y="{y + 72}" fill="#f2f7fc" font-family="Arial,sans-serif" font-size="30" font-weight="700">{value:.3f}</text>',
            f'<rect x="{x + 20}" y="{y + 88}" width="{card_w - 40}" height="7" rx="4" fill="#1b344e"/>',
            f'<rect x="{x + 20}" y="{y + 88}" width="{bar_width:.1f}" height="7" rx="4" fill="#42d9f5"/>',
            f'<text x="{x + 20}" y="{y + 119}" fill="#91a9bf" font-family="Arial,sans-serif" font-size="10">{note}</text>',
        ])
    parts.append('</svg>')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {OUTPUT} from {METRICS}")


if __name__ == "__main__":
    main()
