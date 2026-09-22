import argparse
import json
import re
from pathlib import Path

import yaml


def safe_name(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def convert_af3_to_boltz(af3_data):
    sequences = []

    for entry in af3_data["sequences"]:
        molecule_type = next(iter(entry))
        molecule = entry[molecule_type]

        boltz_entry = {
            molecule_type: {
                "id": molecule["id"],
                "sequence": molecule["sequence"],
            }
        }

        sequences.append(boltz_entry)

    # Find the DNA/RNA aptamer chain.
    aptamer_ids = []

    for entry in af3_data["sequences"]:
        molecule_type = next(iter(entry))

        if molecule_type in {"dna", "rna"}:
            chain_id = entry[molecule_type]["id"]

            if isinstance(chain_id, list):
                aptamer_ids.extend(chain_id)
            else:
                aptamer_ids.append(chain_id)

    if len(aptamer_ids) != 1:
        raise ValueError(
            f"Expected exactly one DNA/RNA aptamer chain, found {aptamer_ids}"
        )

    aptamer_chain = aptamer_ids[0]

    return {
        "version": 1,
        "sequences": sequences,
        "properties": [
            {
                "affinity": {
                    "binder": aptamer_chain
                }
            }
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Convert AF3 input JSON files to Boltz-2 aptamer affinity YAML files."
    )

    parser.add_argument(
        "--input-dir",
        default="af3_inputs",
        help="Directory containing AF3 JSON inputs.",
    )

    parser.add_argument(
        "--output-dir",
        default="boltz_inputs",
        help="Directory to write Boltz YAML files.",
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(input_dir.glob("*.json"))

    if not json_files:
        raise RuntimeError(f"No JSON files found in {input_dir}")

    generated = 0

    for json_path in json_files:
        with json_path.open() as f:
            af3_data = json.load(f)

        job_name = af3_data["name"]
        boltz_data = convert_af3_to_boltz(af3_data)

        output_path = output_dir / f"{job_name}.yaml"

        with output_path.open("w") as f:
            yaml.safe_dump(
                boltz_data,
                f,
                sort_keys=False,
                default_flow_style=False,
            )

        print(f"Wrote {output_path}")
        generated += 1

    print()
    print(f"Generated {generated} Boltz YAML files.")


if __name__ == "__main__":
    main()
