#!/usr/bin/env python3
import csv
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "evaluation" / "android_benchmarks" / "day4"
RUNS_OUTPUT = INPUT_DIR / "day4-all-runs.csv"
SUMMARY_OUTPUT = INPUT_DIR / "day4-model-summary.csv"


def as_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def mean(values: list[float]) -> float:
    clean = [value for value in values if value == value]
    return statistics.mean(clean) if clean else float("nan")


def fmt(value: float, digits: int = 3) -> str:
    if value != value:
        return ""
    return f"{value:.{digits}f}"


def main() -> None:
    csv_files = sorted(
        path for path in INPUT_DIR.glob("day4-*.csv")
        if path.name not in {
            RUNS_OUTPUT.name,
            SUMMARY_OUTPUT.name,
            "day4-quality-analysis.csv",
        }
    )
    if not csv_files:
        raise SystemExit(f"No day4 CSV files found in {INPUT_DIR}")

    rows: list[dict[str, str]] = []
    for csv_file in csv_files:
        with csv_file.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                row["source_csv"] = csv_file.name
                rows.append(row)

    fieldnames = list(rows[0].keys())
    if "source_csv" not in fieldnames:
        fieldnames.append("source_csv")

    with RUNS_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (
            row.get("model_name", ""),
            row.get("quantization", ""),
            row.get("audio_language", ""),
        )
        grouped.setdefault(key, []).append(row)

    summary_rows = []
    for (model_name, quantization, audio_language), group in sorted(grouped.items()):
        inference_times = [as_float(row.get("inference_time_ms", "")) for row in group]
        rtfs = [as_float(row.get("rtf", "")) for row in group]
        java_heap = [as_float(row.get("java_heap_delta_mb", "")) for row in group]
        native_heap = [as_float(row.get("native_heap_delta_mb", "")) for row in group]
        first = group[0]
        summary_rows.append({
            "model_name": model_name,
            "quantization": quantization,
            "audio_language": audio_language,
            "runs": str(len(group)),
            "model_size_mb": first.get("model_size_mb", ""),
            "audio_duration_s": first.get("audio_duration_s", ""),
            "load_time_ms": first.get("load_time_ms", ""),
            "avg_inference_time_ms": fmt(mean(inference_times), 2),
            "avg_rtf": fmt(mean(rtfs), 3),
            "avg_java_heap_delta_mb": fmt(mean(java_heap), 2),
            "avg_native_heap_delta_mb": fmt(mean(native_heap), 2),
            "transcript_preview": first.get("transcript", "")[:160],
        })

    with SUMMARY_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Wrote {RUNS_OUTPUT}")
    print(f"Wrote {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()
