#!/usr/bin/env python3
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "model_benchmark"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def draw_title(draw: ImageDraw.ImageDraw, title: str) -> None:
    draw.text((48, 34), title, fill="#111827", font=font(34, bold=True))


def method_comparison() -> None:
    image = Image.new("RGB", (1400, 820), "white")
    draw = ImageDraw.Draw(image)
    draw_title(draw, "Lightweight ASR Method Comparison")

    methods = ["Quantization", "Distillation", "Pruning", "Recovery Training"]
    metrics = [
        ("Android deployability", [5, 3, 2, 3], "#2563EB"),
        ("Compression potential", [5, 3, 4, 2], "#059669"),
        ("Quality risk", [3, 2, 4, 2], "#D97706"),
        ("Implementation effort", [2, 4, 4, 3], "#7C3AED"),
    ]

    left = 220
    top = 135
    group_gap = 38
    bar_h = 28
    metric_gap = 9
    max_w = 760

    draw.text((48, 92), "Score: 1 low / 5 high", fill="#4B5563", font=font(20))

    for i, method in enumerate(methods):
        y0 = top + i * (len(metrics) * (bar_h + metric_gap) + group_gap)
        draw.text((48, y0 + 38), method, fill="#111827", font=font(22, bold=True))
        for j, (metric, values, color) in enumerate(metrics):
            y = y0 + j * (bar_h + metric_gap)
            value = values[i]
            width = int(max_w * value / 5)
            draw.rounded_rectangle((left, y, left + max_w, y + bar_h), radius=8, fill="#EEF2F7")
            draw.rounded_rectangle((left, y, left + width, y + bar_h), radius=8, fill=color)
            draw.text((left + max_w + 20, y + 1), f"{value}/5", fill="#374151", font=font(19))

    legend_x = 1010
    legend_y = 150
    for i, (metric, _, color) in enumerate(metrics):
        y = legend_y + i * 48
        draw.rectangle((legend_x, y, legend_x + 28, y + 28), fill=color)
        draw.text((legend_x + 42, y), metric, fill="#111827", font=font(20))

    note = "Interpretation: quantization is easiest to deploy; pruning needs sparse runtime support; distillation can improve quality but costs training effort."
    draw.text((48, 760), note, fill="#4B5563", font=font(20))
    image.save(OUT_DIR / "method_comparison.png")


def pruning_tradeoff() -> None:
    image = Image.new("RGB", (1400, 820), "white")
    draw = ImageDraw.Draw(image)
    draw_title(draw, "Pruning Trade-off: Size, Quality, and Runtime Support")

    left, top, width, height = 110, 130, 1080, 520
    draw.rectangle((left, top, left + width, top + height), outline="#CBD5E1", width=2)

    for i in range(0, 101, 20):
        y = top + height - int(height * i / 120)
        draw.line((left, y, left + width, y), fill="#E5E7EB")
        draw.text((54, y - 12), str(i), fill="#6B7280", font=font(18))

    sparsity = [0, 10, 20, 30, 40, 50, 60]
    series = [
        ("Parameter/storage remaining", [100, 90, 80, 70, 60, 50, 40], "#2563EB"),
        ("Expected quality", [100, 99, 97, 94, 88, 78, 62], "#059669"),
        ("Dense runtime speed", [100, 100, 99, 99, 98, 98, 97], "#D97706"),
        ("Sparse-kernel speed potential", [100, 104, 110, 116, 120, 121, 118], "#7C3AED"),
    ]

    def point(x_value: int, y_value: int) -> tuple[int, int]:
        x = left + int(width * x_value / 60)
        y = top + height - int(height * y_value / 125)
        return x, y

    for name, values, color in series:
        points = [point(x, y) for x, y in zip(sparsity, values)]
        draw.line(points, fill=color, width=4)
        for x, y in points:
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color)

    for x in sparsity:
        px, _ = point(x, 0)
        draw.text((px - 12, top + height + 18), str(x), fill="#6B7280", font=font(18))

    draw.text((left + 400, top + height + 58), "Pruning sparsity (%)", fill="#111827", font=font(22, bold=True))
    draw.text((30, top + 210), "Relative value", fill="#111827", font=font(20))

    legend_x = 860
    legend_y = 150
    for i, (name, _, color) in enumerate(series):
        y = legend_y + i * 45
        draw.line((legend_x, y + 14, legend_x + 40, y + 14), fill=color, width=5)
        draw.text((legend_x + 55, y), name, fill="#111827", font=font(20))

    note = "Key point: pruning reduces parameters, but dense mobile runtimes may not convert sparsity into speed."
    draw.text((48, 760), note, fill="#4B5563", font=font(20))
    image.save(OUT_DIR / "pruning_tradeoff.png")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    method_comparison()
    pruning_tradeoff()
    print(f"Wrote {OUT_DIR / 'method_comparison.png'}")
    print(f"Wrote {OUT_DIR / 'pruning_tradeoff.png'}")


if __name__ == "__main__":
    main()
