from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from audit.config import AUDIT_FIELDS, AuditConfig, load_config
from audit.io import read_jsonl, write_json
from audit.sections import (
    build_overview,
    flag_distribution,
    has_blocking_flags_distribution,
    has_migrated_distribution,
    label_distribution,
    lifecycle_coverage,
    missing_field_distribution,
    quality_band_distribution,
    score_total_distribution,
)


def main() -> None:
    config = _build_config(_build_parser().parse_args())
    records = read_jsonl(config.input_path)
    label_records = read_jsonl(config.labels_path)

    audit_document = _build_audit_document(
        config=config,
        records=records,
        label_records=label_records,
    )
    write_json(config.output_path, audit_document)
    _print_summary(audit_document, config.output_path)


def _build_parser() -> argparse.ArgumentParser:
    config = load_config()
    parser = argparse.ArgumentParser(
        description="Build a concise offline dataset audit for filtered snapshots.",
    )
    parser.add_argument(
        "--input-path",
        default=str(config.input_path),
        help="Filtered snapshots JSONL input path.",
    )
    parser.add_argument(
        "--labels-path",
        default=str(config.labels_path),
        help="Optional review labels JSONL input path.",
    )
    parser.add_argument(
        "--output-path",
        default=str(config.output_path),
        help="Audit JSON output path.",
    )
    return parser


def _build_config(args: argparse.Namespace) -> AuditConfig:
    env_config = load_config()
    return AuditConfig(
        input_path=Path(args.input_path),
        labels_path=Path(args.labels_path),
        output_path=Path(args.output_path),
        audit_version=env_config.audit_version,
    )


def _build_audit_document(
    *,
    config: AuditConfig,
    records: list[dict[str, Any]],
    label_records: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "audit_version": config.audit_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_path": str(config.input_path),
        "labels_path": str(config.labels_path),
        "overview": build_overview(records, label_records),
        "quality_band_distribution": quality_band_distribution(records),
        "has_migrated_distribution": has_migrated_distribution(records),
        "has_blocking_flags_distribution": has_blocking_flags_distribution(records),
        "lifecycle_coverage": lifecycle_coverage(records),
        "score_total_distribution": score_total_distribution(records),
        "flag_distribution": flag_distribution(records),
        "label_distribution": label_distribution(records, label_records),
        "missing_field_distribution": missing_field_distribution(records, AUDIT_FIELDS),
    }


def _print_summary(audit_document: dict[str, Any], output_path: Path) -> None:
    overview = audit_document["overview"]
    quality_bands = audit_document["quality_band_distribution"]
    has_migrated = audit_document["has_migrated_distribution"]
    blocking_flags = audit_document["has_blocking_flags_distribution"]
    labels = audit_document["label_distribution"]["counts_by_label"]
    top_missing_fields = sorted(
        audit_document["missing_field_distribution"].items(),
        key=lambda item: (-item[1], item[0]),
    )[:5]

    print(f"Audit written to {output_path}")
    print(
        "records={total_records} migrated={total_migrated_records} blocking={total_blocking_records} complete={total_complete_records}".format(
            **overview
        )
    )
    print(
        "labels labeled={total_labeled_records} orphan={orphan_label_count} by_label={by_label}".format(
            by_label=" ".join(f"{label}={count}" for label, count in labels.items()) or "none",
            **overview,
        )
    )
    print(
        "quality_band weak={weak} partial={partial} strong={strong}".format(
            weak=quality_bands.get("weak", 0),
            partial=quality_bands.get("partial", 0),
            strong=quality_bands.get("strong", 0),
        )
    )
    print(
        "has_migrated false={false} true={true}".format(
            **has_migrated
        )
    )
    print(
        "has_blocking_flags false={false} true={true}".format(
            **blocking_flags
        )
    )
    print(
        "top_missing_fields {fields}".format(
            fields=" ".join(f"{field}={count}" for field, count in top_missing_fields)
        )
    )


if __name__ == "__main__":
    main()
