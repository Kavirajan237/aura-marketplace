from __future__ import annotations
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "entity-fact-audit" / "scripts"
FIXTURES = ROOT / "fixtures"

def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return module

anchor_page = load("anchor_page")
entity_disambiguation = load("entity_disambiguation")
extract_facts = load("extract_facts")

class EntityFactAuditTests(unittest.TestCase):
    def test_complete_identity_is_low_structural_risk_and_extracts_fact(self) -> None:
        result = extract_facts.analyse(FIXTURES / "entity-complete")
        patch = result["twin_patch"]
        self.assertEqual("Orbit", patch["identity"]["name"])
        self.assertEqual("low", patch["identity"]["entity_ambiguity_risk"])
        self.assertEqual("2021", patch["facts"][0]["value"])
        self.assertEqual([], [f for f in result["findings"] if f["check_id"] == "EF-001"])
        self.assertEqual([], [f for f in result["findings"] if f["check_id"] == "EF-005"])
        self.assertTrue(any("EF-007 identity schema types present" in note for note in patch["check_execution"]["checked_and_clean"]))

    def test_common_name_without_sameas_or_qualifier_is_high_risk_without_external_claim(self) -> None:
        result = entity_disambiguation.assess("Atlas", "Tools for teams", {"/index.html": "<h1>Atlas</h1>"})
        self.assertEqual("high", result["risk"])
        self.assertFalse(result["signals"]["authoritative_sameAs_present"])

    def test_smeared_intent_requires_two_partial_pages(self) -> None:
        pages = extract_facts.pages_from_dir(FIXTURES / "entity-smeared")
        result = anchor_page.analyse(pages)
        self.assertEqual("smeared", result["intents"]["pricing"]["status"])
        self.assertEqual("EF-005", result["findings"][0]["check_id"])

    def test_single_partial_page_is_not_a_finding(self) -> None:
        result = anchor_page.analyse({"/one.html": "<p>Pricing details only</p>"})
        self.assertEqual("undetected", result["intents"]["pricing"]["status"])
        self.assertFalse(result["findings"])

    def test_empty_input_emits_insufficient_evidence_and_no_findings(self) -> None:
        result = extract_facts.analyse(FIXTURES / "empty-pages")
        self.assertFalse(result["findings"])
        self.assertEqual("0 readable HTML pages supplied", result["twin_patch"]["check_execution"]["insufficient_evidence"][0]["reason"])

    def test_cli_output_is_json_and_deterministic(self) -> None:
        command = [sys.executable, str(SCRIPTS / "extract_facts.py"), str(FIXTURES / "entity-complete")]
        first = subprocess.run(command, check=True, capture_output=True, text=True).stdout
        second = subprocess.run(command, check=True, capture_output=True, text=True).stdout
        self.assertEqual(first, second); self.assertEqual("Orbit", json.loads(first)["twin_patch"]["identity"]["name"])

if __name__ == "__main__": unittest.main()
