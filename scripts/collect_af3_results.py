import argparse
import csv
import json
import re
from pathlib import Path


def get_chain_ids(sequence_entry):
    """Return (molecule_type, [chain_ids]) from one AF3 sequence entry."""
    molecule_type = next(iter(sequence_entry))
    data = sequence_entry[molecule_type]

    chain_ids = data["id"]
    if isinstance(chain_ids, str):
        chain_ids = [chain_ids]

    return molecule_type.lower(), chain_ids


def parse_serial(job_name):
    """Extract leading UTexas serial number from the AF3 job name."""
    match = re.match(r"^(\d+)", job_name)
    return match.group(1) if match else ""


def unique_preserving_order(values):
    seen = set()
    result = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return result


def find_top_level_summary(output_dir):
    """
    Find the canonical top-level AF3 summary file.

    Ignores summary files inside seed/sample directories.
    """
    matches = list(output_dir.glob("*_summary_confidences.json"))

    if len(matches) == 1:
        return matches[0]

    if len(matches) == 0:
        return None

    raise RuntimeError(
        f"Expected one top-level summary file in {output_dir}, "
        f"found {len(matches)}."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Collect AlphaFold 3 batch results into one CSV."
    )

    parser.add_argument(
        "--input-dir",
        default="af3_inputs",
        help="Directory containing AF3 input JSON files.",
    )

    parser.add_argument(
        "--output-dir",
        default="af3_outputs/batch_1",
        help="Directory containing AF3 output folders.",
    )

    parser.add_argument(
        "--csv",
        default="results/af3_results.csv",
        help="Output CSV path.",
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    csv_path = Path(args.csv)

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for input_path in sorted(input_dir.glob("*.json")):
        with input_path.open() as f:
            input_data = json.load(f)

        job_name = input_data["name"]
        serial_number = parse_serial(job_name)

        protein_chains = []
        aptamer_chains = []
        aptamer_type = ""

        for sequence_entry in input_data["sequences"]:
            molecule_type, chain_ids = get_chain_ids(sequence_entry)

            if molecule_type == "protein":
                protein_chains.extend(chain_ids)

            elif molecule_type in {"dna", "rna"}:
                aptamer_chains.extend(chain_ids)
                aptamer_type = molecule_type.upper()

        # Current project design has one aptamer chain per complex.
        if len(aptamer_chains) != 1:
            print(
                f"WARNING: {job_name} has "
                f"{len(aptamer_chains)} DNA/RNA chains."
            )

        aptamer_chain = aptamer_chains[-1] if aptamer_chains else ""

        job_output_dir = output_dir / job_name
        summary_path = find_top_level_summary(job_output_dir)

        # Count sample-level predictions for auditing.
        sample_summaries = list(
            job_output_dir.glob(
                "seed-*_sample-*/*_summary_confidences.json"
            )
        )

        base_row = {
            "serial_number": serial_number,
            "job_name": job_name,
            "status": "",
            "protein_chains": ",".join(protein_chains),
            "aptamer_chain": aptamer_chain,
            "aptamer_type": aptamer_type,
            "sample_count": len(sample_summaries),
            "ptm": "",
            "iptm": "",
            "ranking_score": "",
            "fraction_disordered": "",
            "has_clash": "",
            "aptamer_chain_ptm": "",
            "aptamer_chain_iptm": "",
            "best_aptamer_protein_iptm": "",
            "min_aptamer_protein_pae": "",
            "interface_iptm_by_chain": "",
            "protein_to_aptamer_pae_by_chain": "",
            "aptamer_to_protein_pae_by_chain": "",
        }

        if not job_output_dir.exists():
            base_row["status"] = "missing output directory"
            rows.append(base_row)
            continue

        if summary_path is None:
            base_row["status"] = "missing top-level summary"
            rows.append(base_row)
            continue

        with summary_path.open() as f:
            summary = json.load(f)

        chain_order = unique_preserving_order(summary["chain_ids"])
        chain_index = {
            chain_id: i for i, chain_id in enumerate(chain_order)
        }

        if aptamer_chain not in chain_index:
            base_row["status"] = "aptamer chain missing from AF3 output"
            rows.append(base_row)
            continue

        aptamer_idx = chain_index[aptamer_chain]

        base_row["status"] = "complete"
        base_row["ptm"] = summary.get("ptm", "")
        base_row["iptm"] = summary.get("iptm", "")
        base_row["ranking_score"] = summary.get("ranking_score", "")
        base_row["fraction_disordered"] = summary.get(
            "fraction_disordered", ""
        )
        base_row["has_clash"] = summary.get("has_clash", "")

        chain_ptm = summary.get("chain_ptm", [])
        chain_iptm = summary.get("chain_iptm", [])

        if aptamer_idx < len(chain_ptm):
            base_row["aptamer_chain_ptm"] = chain_ptm[aptamer_idx]

        if aptamer_idx < len(chain_iptm):
            base_row["aptamer_chain_iptm"] = chain_iptm[aptamer_idx]

        pair_iptm = summary.get("chain_pair_iptm", [])
        pair_pae = summary.get("chain_pair_pae_min", [])

        interface_iptm = {}
        protein_to_aptamer_pae = {}
        aptamer_to_protein_pae = {}

        for protein_chain in protein_chains:
            if protein_chain not in chain_index:
                continue

            protein_idx = chain_index[protein_chain]

            if pair_iptm:
                interface_iptm[protein_chain] = pair_iptm[
                    protein_idx
                ][aptamer_idx]

            if pair_pae:
                protein_to_aptamer_pae[protein_chain] = pair_pae[
                    protein_idx
                ][aptamer_idx]

                aptamer_to_protein_pae[protein_chain] = pair_pae[
                    aptamer_idx
                ][protein_idx]

        if interface_iptm:
            base_row["best_aptamer_protein_iptm"] = max(
                interface_iptm.values()
            )

        all_interface_pae = (
            list(protein_to_aptamer_pae.values())
            + list(aptamer_to_protein_pae.values())
        )

        if all_interface_pae:
            base_row["min_aptamer_protein_pae"] = min(
                all_interface_pae
            )

        # Store per-protein-chain values without losing information.
        base_row["interface_iptm_by_chain"] = json.dumps(
            interface_iptm,
            sort_keys=True,
        )

        base_row["protein_to_aptamer_pae_by_chain"] = json.dumps(
            protein_to_aptamer_pae,
            sort_keys=True,
        )

        base_row["aptamer_to_protein_pae_by_chain"] = json.dumps(
            aptamer_to_protein_pae,
            sort_keys=True,
        )

        rows.append(base_row)

    fieldnames = [
        "serial_number",
        "job_name",
        "status",
        "protein_chains",
        "aptamer_chain",
        "aptamer_type",
        "sample_count",
        "ptm",
        "iptm",
        "ranking_score",
        "fraction_disordered",
        "has_clash",
        "aptamer_chain_ptm",
        "aptamer_chain_iptm",
        "best_aptamer_protein_iptm",
        "min_aptamer_protein_pae",
        "interface_iptm_by_chain",
        "protein_to_aptamer_pae_by_chain",
        "aptamer_to_protein_pae_by_chain",
    ]

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    complete = sum(row["status"] == "complete" for row in rows)

    print(f"Wrote {len(rows)} AF3 records to {csv_path}")
    print(f"Complete: {complete}")
    print(f"Incomplete: {len(rows) - complete}")


if __name__ == "__main__":
    main()
