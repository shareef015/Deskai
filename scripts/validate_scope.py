#!/usr/bin/env python3
"""Validate the authoritative DeskPilot product-scope contracts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"


def load(name: str) -> dict:
    with (CONTRACTS / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def validate() -> list[str]:
    errors: list[str] = []
    scope = load("product-scope.json")
    windows = load("windows-support-policy.json")
    incidents = load("incident-catalog.json")
    consent = load("consent-policy.json")
    commercial = load("commercial-boundaries.json")

    expected_os = {"windows_10", "windows_11"}
    actual_os = set(scope["product"]["managed_endpoint_operating_systems"])
    if actual_os != expected_os:
        errors.append(f"Managed endpoint OS set must be {expected_os}, got {actual_os}")

    if scope["product"]["initial_pilot_device_limit"] != 10:
        errors.append("Initial pilot must be limited to 10 managed endpoints")

    win10 = windows["platforms"]["windows_10"]
    if win10["final_feature_release"] != "22H2":
        errors.append("Windows 10 final feature release must be 22H2")
    if not set(win10["full_operation_requires_one_of"]):
        errors.append("Windows 10 full-operation eligibility must be explicit")

    required_domains = {"outlook", "printer", "scanner", "windows_connectivity"}
    if set(incidents["domains"]) != required_domains:
        errors.append("Incident catalogue domains are incomplete or out of scope")

    if not consent["diagnostic_consent"]["must_precede_endpoint_session"]:
        errors.append("Diagnostic consent must precede endpoint access")
    if not consent["remediation_consent"]["separate_from_diagnostics"]:
        errors.append("Remediation authorization must be separate")

    prohibited = set(scope["prohibited_capabilities"])
    for capability in {
        "unrestricted_remote_shell",
        "credential_or_token_extraction",
        "authorization_decided_by_llm",
        "incident_closure_from_exit_code_only",
    }:
        if capability not in prohibited:
            errors.append(f"Missing prohibited capability: {capability}")

    if commercial["external_data_transfer"]["default"] != "denied":
        errors.append("External data transfer must be denied by default")
    if commercial["proposed_editions"]["pilot"]["real_devices"] != 10:
        errors.append("Pilot commercial boundary must be 10 real devices")

    return errors


if __name__ == "__main__":
    validation_errors = validate()
    if validation_errors:
        for error in validation_errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("DeskPilot scope contracts are valid.")
