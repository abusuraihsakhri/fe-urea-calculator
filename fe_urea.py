#!/usr/bin/env python3
"""
Fractional Excretion of Urea (FEUrea) Calculator
Differentiates prerenal azotemia from acute tubular necrosis when diuretics invalidate FENa.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT

FEUrea Formula:
    FEUrea = (Urine_Urea * Serum_Creatinine) / (Serum_Urea * Urine_Creatinine) * 100

Clinical Interpretation:
    - FEUrea < 35%: Suggests prerenal azotemia (kidneys conserving urea)
    - FEUrea >= 35%: Suggests acute tubular necrosis (ATN) or intrinsic renal disease

Reference: KDIGO & KDOQI Clinical Practice Guidelines
"""

import argparse
import csv
import json
import sys
from typing import Dict, Any, List, Optional


class ValidationError(Exception):
    """Raised when input parameters fail validation."""
    pass


def calculate_fe_urea(serum_creatinine: float, urine_creatinine: float,
                      serum_urea: float, urine_urea: float) -> Dict[str, Any]:
    """
    Calculate Fractional Excretion of Urea (FEUrea).

    Args:
        serum_creatinine: Serum creatinine concentration (mg/dL)
        urine_creatinine: Urine creatinine concentration (mg/dL)
        serum_urea: Serum urea concentration (mg/dL)
        urine_urea: Urine urea concentration (mg/dL)

    Returns:
        Dictionary containing FEUrea score, classification, and clinical recommendation.

    Raises:
        ValidationError: If any input is invalid (non-positive or non-numeric).
        ZeroDivisionError: If denominator values are zero.
    """
    # Validate inputs
    params = {
        "serum_creatinine": serum_creatinine,
        "urine_creatinine": urine_creatinine,
        "serum_urea": serum_urea,
        "urine_urea": urine_urea,
    }

    for name, value in params.items():
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{name} must be numeric, got {type(value).__name__}")
        if value <= 0:
            raise ValidationError(f"{name} must be positive, got {value}")

    # FEUrea = (Urine_Urea * Serum_Creatinine) / (Serum_Urea * Urine_Creatinine) * 100
    fe_urea = (urine_urea * serum_creatinine) / (serum_urea * urine_creatinine) * 100
    rounded_score = round(fe_urea, 2)

    # Clinical classification based on KDIGO/KDOQI guidelines
    if fe_urea < 35.0:
        classification = "Prerenal Azotemia"
        recommendation = ("FEUrea < 35% suggests prerenal state. "
                          "Consider volume resuscitation and hemodynamic optimization.")
    else:
        classification = "Acute Tubular Necrosis / Intrinsic Renal Disease"
        recommendation = ("FEUrea >= 35% suggests ATN or intrinsic renal pathology. "
                          "Avoid volume overload; consider nephrology consultation.")

    return {
        "tool": "fe-urea-calculator",
        "fe_urea_percent": rounded_score,
        "classification": classification,
        "clinical_recommendation": recommendation,
        "inputs": params,
    }


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """
    Legacy compatibility wrapper for fe-urea-calculator.
    Accepts v1, v2, v3 parameters mapped to the FEUrea formula inputs.

    Mapping:
        v1 -> serum_creatinine
        v2 -> urine_creatinine
        v3 -> serum_urea
        urine_urea defaults to v1 * 10 (typical ratio) if not provided
    """
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            try:
                params[k] = float(v)
            except (ValueError, TypeError):
                params[k] = str(v)

    # Extract numeric values with defaults for FEUrea calculation
    serum_creatinine = params.get("serum_creatinine", params.get("v1", 1.0))
    urine_creatinine = params.get("urine_creatinine", params.get("v2", 100.0))
    serum_urea = params.get("serum_urea", params.get("v3", params.get("v1", 1.0) * 2))
    urine_urea = params.get("urine_urea", params.get("v1", 1.0) * 10)

    return calculate_fe_urea(serum_creatinine, urine_creatinine, serum_urea, urine_urea)


def process_single(args) -> None:
    kwargs = vars(args)
    kwargs.pop("func", None)
    kwargs.pop("command", None)
    res = calculate_metrics(**kwargs)
    print(json.dumps(res, indent=2))


def process_batch(input_csv: str, output_csv: str) -> None:
    """Process batch CSV file with FEUrea calculations.

    Expected CSV columns: serum_creatinine, urine_creatinine, serum_urea, urine_urea
    Legacy columns (v1, v2, v3) are also supported for backward compatibility.
    """
    try:
        with open(input_csv, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)
    except FileNotFoundError:
        print(f"Error: Input file '{input_csv}' not found.", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied reading '{input_csv}'.", file=sys.stderr)
        sys.exit(1)

    out_fields = fieldnames + ["fe_urea_percent", "classification", "clinical_recommendation"]
    out_rows = []
    errors = []

    for idx, r in enumerate(rows, start=1):
        try:
            calc_res = calculate_metrics(**r)
            row_dict = dict(r)
            row_dict["fe_urea_percent"] = calc_res["fe_urea_percent"]
            row_dict["classification"] = calc_res["classification"]
            row_dict["clinical_recommendation"] = calc_res["clinical_recommendation"]
            out_rows.append(row_dict)
        except (ValidationError, ZeroDivisionError) as e:
            errors.append(f"Row {idx}: {e}")
            row_dict = dict(r)
            row_dict["fe_urea_percent"] = "ERROR"
            row_dict["classification"] = "INVALID_INPUT"
            row_dict["clinical_recommendation"] = str(e)
            out_rows.append(row_dict)

    try:
        with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
    except PermissionError:
        print(f"Error: Permission denied writing '{output_csv}'.", file=sys.stderr)
        sys.exit(1)

    print(f"Processed {len(out_rows)} records -> {output_csv}")
    if errors:
        print(f"  {len(errors)} row(s) had errors:")
        for err in errors:
            print(f"    - {err}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fractional Excretion of Urea (FEUrea) Calculator",
        epilog="FEUrea = (Urine_Urea * Serum_Creatinine) / (Serum_Urea * Urine_Creatinine) * 100"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single parser
    single_parser = subparsers.add_parser("single", help="Evaluate single case")
    single_parser.add_argument("--serum-creatinine", type=float, default=1.0,
                               help="Serum creatinine (mg/dL)")
    single_parser.add_argument("--urine-creatinine", type=float, default=100.0,
                               help="Urine creatinine (mg/dL)")
    single_parser.add_argument("--serum-urea", type=float, default=20.0,
                               help="Serum urea (mg/dL)")
    single_parser.add_argument("--urine-urea", type=float, default=200.0,
                               help="Urine urea (mg/dL)")
    single_parser.set_defaults(func=process_single)

    # Batch parser
    batch_parser = subparsers.add_parser("batch", help="Process batch CSV")
    batch_parser.add_argument("-i", "--input", required=True, help="Input CSV file path")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Output CSV file path")

    args = parser.parse_args(argv)

    if args.command == "single":
        args.func(args)
    elif args.command == "batch":
        process_batch(args.input, args.output)


if __name__ == "__main__":
    main()
