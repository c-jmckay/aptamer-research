import argparse
import csv
import json
import re
from pathlib import Path


def parse_serial(job_name):
    match = re.match(r"^(\d+)", job_name)
    return match.group(1) if match else ""


def main():
    parser = argparse.ArgumentParser(
        description="Collect Boltz-2 affinity predictions into one CSV."
    )

    parser.add_argument(
        "--predictions-dir",
        default=(
            "boltz_outputs/batch_1/"
            "boltz_results_boltz_inputs/predictions"
        ),
        help="Directory containing Boltz prediction folders.",
    )

    parser.add_argument(
        "--csv",
        default="results/boltz_results.csv",
        help="Output CSV path.",
    )

    args = parser.parse_args()

    predictions_dir = Path(args.predictions_dir)
    csv_path = Path(args.csv)

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for prediction_dir in sorted(predictions_dir.iterdir()):
        if not prediction_dir.is_dir():
            continue

        job_name = prediction_dir.name
        serial_number = parse_serial(job_name)

        affinity_path = (
            prediction_dir / f"affinity_{job_name}.json"
        )

        row = {
            "serial_number": serial_number,
            "job_name": job_name,
            "status": "",
            "affinity_pred_value": "",
            "affinity_pred_value1": "",
            "affinity_pred_value2": "",
            "affinity_probability_binary": "",
            "affinity_probability_binary1": "",
            "affinity_probability_binary2": "",
        }

        if not affinity_path.exists():
            row["status"] = "missing affinity json"
            rows.append(row)
            continue

        try:
            with affinity_path.open() as f:
                affinity = json.load(f)
        except Exception as exc:
            row["status"] = f"json read error: {exc}"
            rows.append(row)
            continue

        row["status"] = "complete"

        for key in [
            "affinity_pred_value",
            "affinity_pred_value1",
            "affinity_pred_value2",
            "affinity_probability_binary",
            "affinity_probability_binary1",
            "affinity_probability_binary2",
        ]:
            row[key] = affinity.get(key, "")

        rows.append(row)

    fieldnames = [
        "serial_number",
        "job_name",
        "status",
        "affinity_pred_value",
        "affinity_pred_value1",
        "affinity_pred_value2",
        "affinity_probability_binary",
        "affinity_probability_binary1",
        "affinity_probability_binary2",
    ]

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)

    complete = sum(
        row["status"] == "complete"
        for row in rows
    )

    print(f"Wrote {len(rows)} Boltz records to {csv_path}")
    print(f"Complete: {complete}")
    print(f"Incomplete: {len(rows) - complete}")


if __name__ == "__main__":
    main()
