"""Tests for the CLI's --dashboard-data output - no live credentials."""
import json
import os
import sys

from framework.cli import main

CLARIO_CONFIG = os.path.join(
    os.path.dirname(__file__), "..", "examples", "clario", "config.yaml"
)
CLARIO_DIR = os.path.join(os.path.dirname(__file__), "..", "examples", "clario")


def _run_scan_with_dashboard_data(tmp_path, monkeypatch, extra_args=None):
    out_path = tmp_path / "dashboard-data.js"
    argv = [
        "prog",
        "scan",
        "--config",
        CLARIO_CONFIG,
        "--target",
        CLARIO_DIR,
        "--dashboard-data",
        str(out_path),
    ] + (extra_args or [])
    monkeypatch.setattr(sys, "argv", argv)
    exit_code = main()
    assert exit_code == 0
    return out_path


def _parse_dashboard_js(path):
    text = path.read_text()
    assert text.startswith("window.MCP_READINESS_DATA = ")
    assert text.rstrip().endswith(";")
    payload = text[len("window.MCP_READINESS_DATA = ") : text.rstrip().rfind(";")]
    return json.loads(payload)


def test_dashboard_data_file_is_written(tmp_path, monkeypatch):
    out_path = _run_scan_with_dashboard_data(tmp_path, monkeypatch)
    assert out_path.exists()


def test_dashboard_data_is_valid_loadable_json(tmp_path, monkeypatch):
    out_path = _run_scan_with_dashboard_data(tmp_path, monkeypatch)
    data = _parse_dashboard_js(out_path)
    assert data["target"] == "Clario Expense & Invoicing API"
    assert 1 <= data["overall_level"] <= 4


def test_dashboard_data_has_all_six_dimensions_with_check_detail(tmp_path, monkeypatch):
    out_path = _run_scan_with_dashboard_data(tmp_path, monkeypatch)
    data = _parse_dashboard_js(out_path)
    dim_ids = {d["id"] for d in data["dimensions"]}
    assert dim_ids == {
        "write_safety",
        "boundary_enforcement",
        "consent_auth",
        "forensics",
        "interface_legibility",
        "operational_containment",
    }
    for dim in data["dimensions"]:
        assert 1 <= dim["level"] <= 4
        assert len(dim["check_results"]) > 0
        for check in dim["check_results"]:
            assert set(check.keys()) == {
                "id",
                "description",
                "passed",
                "evidence",
                "score_contribution",
            }


def test_dashboard_data_matches_plain_json_output(tmp_path, monkeypatch):
    """--dashboard-data is the same scorecard shape as --output, just JS-wrapped."""
    json_out_path = tmp_path / "scorecard.json"
    dashboard_out_path = _run_scan_with_dashboard_data(
        tmp_path, monkeypatch, extra_args=["--output", str(json_out_path)]
    )
    plain = json.loads(json_out_path.read_text())
    dashboard = _parse_dashboard_js(dashboard_out_path)
    assert plain == dashboard
