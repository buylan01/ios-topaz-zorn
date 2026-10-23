#!/usr/bin/env python3
"""Validate the zorn research manifest without promoting guesses to hardware config."""
import json
import sys
from pathlib import Path

VALID_STATUS = {"observed", "candidate", "inferred", "unknown", "verified"}
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research/zorn/hardware-manifest.json"


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def walk(value, path="$"):
    if isinstance(value, dict):
        if "status" in value and value["status"] not in VALID_STATUS:
            fail(f"{path}.status has invalid value {value['status']!r}")
        if "value" in value and value.get("status") == "unknown" and value["value"] is not None:
            fail(f"{path}: unknown status must not contain a value")
        for key, child in value.items():
            walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            walk(child, f"{path}[{i}]")


def main():
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read valid JSON manifest: {exc}")

    if data.get("schema_version") != 1:
        fail("schema_version must be 1")
    for key in ("device", "boot_chain", "cpu", "interrupts", "debug", "memory", "storage", "display", "safety"):
        if key not in data:
            fail(f"missing required top-level section: {key}")
    if data["device"].get("codename") != "zorn" or data["device"].get("soc") != "Qualcomm SM8650":
        fail("device identity does not match Redmi K80 / zorn / SM8650")
    if data["cpu"].get("smp_enabled") is not False:
        fail("SMP must remain disabled until CPU0 bring-up and per-core probing are verified")
    if data["memory"].get("status") != "blocked" and not data["memory"].get("normalized_regions"):
        fail("memory cannot be unblocked without normalized memory regions")
    safety = data["safety"]
    for key in ("partition_writes_performed", "userdata_modified", "destructive_install_allowed"):
        if safety.get(key) is not False:
            fail(f"safety.{key} must remain false in this research-only milestone")
    if data["storage"].get("root_volume_write_allowed") is not False:
        fail("root-volume writes must remain disabled")
    walk(data)
    print("zorn hardware manifest: PASS (research-only; not a boot configuration)")
    print("SMP: disabled; memory allocator: blocked; storage writes: disabled; partition writes: none")


if __name__ == "__main__":
    main()
