#!/usr/bin/env python3
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DAY4_DIR = ROOT / "benchmarks" / "day4"
SUMMARY_CSV = DAY4_DIR / "day4-model-summary.csv"
ALL_RUNS_CSV = DAY4_DIR / "day4-all-runs.csv"

REFERENCE_TEXT = "这是 ASR Mobile 项目的第四天正式测试。我们正在比较不同量化模型在华为手机上的离线语音识别速度和识别质量。"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def levenshtein(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (0 if ca == cb else 1),
            ))
        previous = current
    return previous[-1]


def normalize_for_cer(text: str) -> str:
    return "".join(
        char.lower()
        for char in text
        if not char.isspace() and not re.match(r"[，。！？、,.!?;:：；\"'`“”‘’()（）-]", char)
    )


def tokenize_for_wer(text: str) -> list[str]:
    normalized = text.lower()
    normalized = re.sub(r"[，。！？、,.!?;:：；\"'`“”‘’()（）-]", " ", normalized)
    tokens: list[str] = []
    for part in normalized.split():
        tokens.extend(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]|.", part))
    return tokens


def token_distance(a: list[str], b: list[str]) -> int:
    previous = list(range(len(b) + 1))
    for i, token_a in enumerate(a, 1):
        current = [i]
        for j, token_b in enumerate(b, 1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (0 if token_a == token_b else 1),
            ))
        previous = current
    return previous[-1]


def quality_score(cer: float) -> int:
    if cer <= 0.20:
        return 5
    if cer <= 0.35:
        return 4
    if cer <= 0.50:
        return 3
    if cer <= 0.70:
        return 2
    return 1


def write_quality_csv(rows: list[dict[str, str]]) -> None:
    output = DAY4_DIR / "day4-quality-analysis.csv"
    grouped: dict[str, list[str]] = {}
    for row in rows:
        grouped.setdefault(row["model_name"], []).append(row["transcript"])

    with output.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "model_name",
            "runs",
            "avg_cer",
            "avg_wer",
            "quality_score",
            "representative_transcript",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        reference_chars = normalize_for_cer(REFERENCE_TEXT)
        reference_tokens = tokenize_for_wer(REFERENCE_TEXT)
        for model_name, transcripts in sorted(grouped.items()):
            cers = [
                levenshtein(reference_chars, normalize_for_cer(transcript)) / max(1, len(reference_chars))
                for transcript in transcripts
            ]
            wers = [
                token_distance(reference_tokens, tokenize_for_wer(transcript)) / max(1, len(reference_tokens))
                for transcript in transcripts
            ]
            avg_cer = sum(cers) / len(cers)
            avg_wer = sum(wers) / len(wers)
            writer.writerow({
                "model_name": model_name,
                "runs": len(transcripts),
                "avg_cer": f"{avg_cer:.3f}",
                "avg_wer": f"{avg_wer:.3f}",
                "quality_score": quality_score(avg_cer),
                "representative_transcript": transcripts[0],
            })
    print(f"Wrote {output}")


def svg_bar_chart(
    output: Path,
    title: str,
    rows: list[dict[str, str]],
    value_key: str,
    label_key: str = "model_name",
    unit: str = "",
    width: int = 960,
    bar_height: int = 34,
) -> None:
    margin_left = 220
    margin_right = 120
    margin_top = 70
    gap = 18
    height = margin_top + len(rows) * (bar_height + gap) + 60
    values = [float(row[value_key]) for row in rows if row.get(value_key)]
    max_value = max(values) if values else 1.0
    plot_width = width - margin_left - margin_right
    colors = ["#246BFE", "#1F9D78", "#D9822B", "#7C3AED", "#64748B"]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="32" y="38" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="#111827">{title}</text>',
    ]

    for index, row in enumerate(rows):
        value = float(row[value_key])
        label = row[label_key]
        bar_width = value / max_value * plot_width
        y = margin_top + index * (bar_height + gap)
        color = colors[index % len(colors)]
        parts.extend([
            f'<text x="32" y="{y + 23}" font-family="Arial, sans-serif" font-size="16" fill="#111827">{label}</text>',
            f'<rect x="{margin_left}" y="{y}" width="{plot_width}" height="{bar_height}" fill="#EEF2F7" rx="4"/>',
            f'<rect x="{margin_left}" y="{y}" width="{bar_width:.2f}" height="{bar_height}" fill="{color}" rx="4"/>',
            f'<text x="{margin_left + bar_width + 12:.2f}" y="{y + 23}" font-family="Arial, sans-serif" font-size="15" fill="#374151">{value:.3f}{unit}</text>',
        ])

    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {output}")


def main() -> None:
    summary_rows = read_csv(SUMMARY_CSV)
    run_rows = read_csv(ALL_RUNS_CSV)
    summary_rows = sorted(summary_rows, key=lambda row: float(row["avg_rtf"]))

    write_quality_csv(run_rows)
    svg_bar_chart(
        output=DAY4_DIR / "day4-size-comparison.svg",
        title="Day 4 Model Size Comparison",
        rows=summary_rows,
        value_key="model_size_mb",
        unit=" MB",
    )
    svg_bar_chart(
        output=DAY4_DIR / "day4-rtf-comparison.svg",
        title="Day 4 Average RTF Comparison",
        rows=summary_rows,
        value_key="avg_rtf",
        unit="",
    )


if __name__ == "__main__":
    main()
