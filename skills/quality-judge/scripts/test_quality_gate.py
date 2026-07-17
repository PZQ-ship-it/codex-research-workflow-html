#!/usr/bin/env python3
"""Regression tests for quality_gate.py."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

import quality_gate


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class QualityGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run_dir = Path(self.temp.name)
        quality_gate.init_run(self.run_dir)
        self.config = quality_gate.load_json(self.run_dir / "gate-config.json")
        self.dimensions = self.config["dimensions"]
        self._write_core(candidate_score=4.6)

    def _write_core(self, candidate_score: float, structural_pass: bool = True) -> None:
        write_json(self.run_dir / "structural-result.json", {
            "reviewer": "structural_reviewer",
            "pass": structural_pass,
            "critical_failures": [] if structural_pass else ["hard failure"],
            "evidence": [{"claim": "checked", "locator": "artifact.txt"}],
            "fixes": [],
        })
        write_json(self.run_dir / "quality-result.json", {
            "reviewer": "quality_judge",
            "scoring_lane": "reference-scorer-001",
            "dimension_scores": {dimension: candidate_score for dimension in self.dimensions},
            "confidence": 0.9,
            "calibration": {"human_anchored": False, "leniency": 0.0, "agreement": {}},
            "evidence": [{"dimension": self.dimensions[0], "locator": "artifact.txt", "claim": "evidence"}],
            "reference_comparisons": [],
            "counterexamples": [],
            "revision_actions": [],
        })

    def _human_reference(self, graded_by: str = "human") -> None:
        write_json(self.run_dir / "human-reference.json", {
            "reference_id": "human-001",
            "graded_by": graded_by,
            "grader_count": 2 if graded_by == "human" else 1,
            "rubric_version": self.config["rubric_version"],
            "dimension_scores": {dimension: 4.0 for dimension in self.dimensions},
            "notes": "test",
        })

    def _build_retrieved(self, outcomes: list[str], tier: str = "retrieved_verified") -> None:
        queries = [
            {"query_id": "q-001", "query": "strong public example"},
            {"query_id": "q-002", "query": "best comparable artifact"},
        ]
        entries: list[dict[str, Any]] = []
        references: list[dict[str, Any]] = []
        comparisons: list[dict[str, Any]] = []
        prompt_hash = "b" * 64
        rubric_hash = quality_gate.sha256(self.run_dir / "rubric.json")

        for index, outcome in enumerate(outcomes, start=1):
            candidate_id = f"candidate-{index:03d}"
            reference_id = f"ref-{index:03d}"
            snapshot = self.run_dir / "snapshots" / f"{reference_id}.txt"
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_text(f"reference {index}\n", encoding="utf-8")
            snapshot_hash = quality_gate.sha256(snapshot)
            source_url = f"https://example.org/{reference_id}"
            source_date = "2026-07-17"
            retrieved_at = "2026-07-17T12:00:00Z"
            entries.append({
                "candidate_id": candidate_id,
                "query_ids": ["q-001", "q-002"],
                "result_ranks": [index, index + 1],
                "source_url": source_url,
                "source_date": source_date,
                "retrieved_at": retrieved_at,
                "license_or_access_basis": "public-page",
                "snapshot_locator": f"snapshots/{reference_id}.txt",
                "content_sha256": snapshot_hash,
                "mime_type": "text/plain",
                "size_bytes": snapshot.stat().st_size,
                "active_content_neutralized": True,
                "remote_resources_disabled": True,
                "suspicious_content": False,
                "included": True,
                "decision_reason": "hard-comparable frontier reference",
            })
            reference_score = 4.0 if outcome == "candidate" else 4.8
            verification_dimensions = {
                dimension: {
                    "status": "verified",
                    "method": "official_source",
                    "evidence_locators": [f"snapshots/{reference_id}.txt"],
                    "verified_by": "verifier-001",
                    "verifier_independence": "independent",
                    "verified_at": retrieved_at,
                }
                for dimension in self.config["critical_dimensions"]
            }
            scoring_dimensions = {
                dimension: {
                    "score": reference_score,
                    "evidence_locators": [f"snapshots/{reference_id}.txt"],
                    "judge_id": "reference-scorer-001",
                    "model": "test-model",
                    "prompt_sha256": prompt_hash,
                    "trial_ids": [f"score-{reference_id}-{dimension}"],
                    "conflict_state": "none",
                }
                for dimension in self.dimensions
            }
            verification = {
                "status": "verified" if tier == "retrieved_verified" else "unverified",
                "dimensions": verification_dimensions if tier == "retrieved_verified" else {},
                "conflicts": [],
            }
            references.append({
                "reference_id": reference_id,
                "source_candidate_id": candidate_id,
                "frontier": True,
                "tier": tier,
                "source_url": source_url,
                "source_date": source_date,
                "retrieved_at": retrieved_at,
                "content_sha256": snapshot_hash,
                "license_or_access_basis": "public-page",
                "authorship": "human",
                "selection": {
                    "query_ids": ["q-001", "q-002"],
                    "result_ranks": [index, index + 1],
                    "inclusion_reason": "hard-comparable frontier reference",
                },
                "verification": verification,
                "comparability": {"hard_pass": True, "reasons": ["same task contract"]},
                "scoring": {
                    "rubric_version": self.config["rubric_version"],
                    "rubric_sha256": rubric_hash,
                    "dimensions": scoring_dimensions,
                    "conflicts": [],
                },
            })
            if outcome == "candidate":
                candidate_first = ["candidate"] * 3
                reference_first = ["candidate"] * 3
            elif outcome == "reference":
                candidate_first = ["reference"] * 3
                reference_first = ["reference"] * 3
            else:
                candidate_first = ["candidate"] * 3
                reference_first = ["reference"] * 3
            comparisons.append({
                "reference_id": reference_id,
                "candidate_first": candidate_first,
                "reference_first": reference_first,
                "bias_audit": {
                    "verbosity_relation": "similar",
                    "format_relation": "none",
                    "source_family_overlap": False,
                    "judge_family_overlap": "unknown",
                    "suspected_confounds": [],
                    "unresolved": False,
                },
            })

        ledger = {
            "schema_version": "1.0",
            "provider": "test-search",
            "queries": queries,
            "searched_at": "2026-07-17T12:00:00Z",
            "entries": entries,
        }
        write_json(self.run_dir / "candidate-pool-ledger.json", ledger)
        policy_dimensions = {
            dimension: {
                "weight": self.config["weights"][dimension],
                "floor": self.config["critical_floor"] if dimension in self.config["critical_dimensions"] else self.config["scale"]["min"],
                "critical": dimension in self.config["critical_dimensions"],
            }
            for dimension in self.dimensions
        }
        reference_set = {
            "schema_version": "1.1",
            "mode": "retrieved_provisional",
            "task_fingerprint": {
                "artifact_type": "research_note",
                "audience": "technical stakeholder",
                "fingerprint_minimized": True,
                "outbound_query_safe": True,
                "contains_private_data": False,
                "rubric_version": self.config["rubric_version"],
                "critical_dimensions": self.config["critical_dimensions"],
            },
            "evaluation_policy": {
                "policy_version": "1.1",
                "policy_sha256": quality_gate.sha256(self.run_dir / "gate-config.json"),
                "rubric_version": self.config["rubric_version"],
                "rubric_locator": "rubric.json",
                "rubric_sha256": rubric_hash,
                "reference_margin": self.config["reference_margin"],
                "dimensions": policy_dimensions,
                "scoring_lanes": ["reference-scorer-001"],
            },
            "retrieval": {
                "status": "completed",
                "provider": "test-search",
                "queries": queries,
                "searched_at": "2026-07-17T12:00:00Z",
                "selector_blinded_to_candidate": True,
                "pool_size": len(entries),
                "reference_set_frozen": True,
                "candidate_pool_ledger": {
                    "locator": "candidate-pool-ledger.json",
                    "sha256": quality_gate.sha256(self.run_dir / "candidate-pool-ledger.json"),
                    "entry_count": len(entries),
                },
                "selector": {
                    "selector_id": "selector-001",
                    "model": "test-selector",
                    "prompt_sha256": "c" * 64,
                    "independence": "model",
                },
            },
            "references": references,
            "aggregation": {
                "method": "pareto_frontier",
                "pairwise_order_swap": True,
                "require_no_critical_regression": True,
                "artifact_level": {
                    "trials_per_order": 3,
                    "decision_rule": "unanimous_across_orders_and_trials",
                    "confidence_intervals": False,
                },
            },
        }
        write_json(self.run_dir / "reference-set.json", reference_set)
        quality = quality_gate.load_json(self.run_dir / "quality-result.json")
        quality["reference_comparisons"] = comparisons
        write_json(self.run_dir / "quality-result.json", quality)

    def _build_retrieved_v12(
        self,
        outcomes: list[str],
        *,
        roles: list[list[str]] = None,
        bands: list[str] = None,
        band_provenances: list[str] = None,
        reference_scores: list[float] = None,
        tier: str = "retrieved_verified",
    ) -> None:
        self._build_retrieved(outcomes, tier=tier)
        count = len(outcomes)
        roles = roles or [["calibration_anchor", "challenge_frontier"] for _ in range(count)]
        bands = bands or ["high" for _ in range(count)]
        band_provenances = band_provenances or ["independent_judge" for _ in range(count)]
        if not (len(roles) == len(bands) == len(band_provenances) == count):
            raise AssertionError("v1.2 reference metadata must align")

        artifact = self.run_dir / "artifact.txt"
        artifact.write_text("candidate artifact\n", encoding="utf-8")
        write_json(self.run_dir / "task-contract.json", {
            "schema_version": "1.0",
            "artifact_type": "research_note",
            "audience": "technical stakeholder",
            "use_case": "make a review decision",
            "goals": ["judge holistic quality"],
            "constraints": ["preserve human-only acceptance"],
            "non_goals": ["repeat structural checks"],
            "quality_outcomes": ["decision-useful and coherent output"],
            "candidate_sha256": quality_gate.sha256(artifact),
        })

        reference_set = quality_gate.load_json(self.run_dir / "reference-set.json")
        reference_set["schema_version"] = "1.2"
        reference_set["evaluation_policy"]["policy_version"] = "1.2"
        reference_set["evaluation_policy"]["absolute_quality_floor"] = self.config["absolute_quality_floor"]
        for dimension in self.dimensions:
            reference_set["evaluation_policy"]["dimensions"][dimension]["floor"] = self.config["dimension_floors"][dimension]
        reference_set["aggregation"]["method"] = "anchor_panel_plus_frontier"
        reference_set["aggregation"]["anchor_panel"] = self.config["reference_fallback"]["anchor_panel"]

        reference_ids: list[str] = []
        frontier_ids: set[str] = set()
        for index, reference in enumerate(reference_set["references"]):
            reference_id = reference["reference_id"]
            reference_ids.append(reference_id)
            reference["roles"] = roles[index]
            reference["quality_band"] = bands[index]
            reference["band_provenance"] = band_provenances[index]
            if "challenge_frontier" in roles[index]:
                frontier_ids.add(reference_id)
            if reference_scores is not None:
                for dimension in self.dimensions:
                    reference["scoring"]["dimensions"][dimension]["score"] = reference_scores[index]

        rubric = quality_gate.load_json(self.run_dir / "rubric.json")
        rubric["generation"]["task_contract_sha256"] = quality_gate.sha256(self.run_dir / "task-contract.json")
        rubric["generation"]["example_audit"] = {
            "performed": True,
            "reference_ids": reference_ids,
            "dimension_proposals": [],
            "rubric_refrozen_after_audit": True,
        }
        write_json(self.run_dir / "rubric.json", rubric)
        rubric_hash = quality_gate.sha256(self.run_dir / "rubric.json")
        reference_set["evaluation_policy"]["rubric_sha256"] = rubric_hash
        for reference in reference_set["references"]:
            reference["scoring"]["rubric_sha256"] = rubric_hash
        write_json(self.run_dir / "reference-set.json", reference_set)

        ledger = quality_gate.load_json(self.run_dir / "candidate-pool-ledger.json")
        ledger["schema_version"] = "1.1"
        write_json(self.run_dir / "candidate-pool-ledger.json", ledger)
        reference_set = quality_gate.load_json(self.run_dir / "reference-set.json")
        reference_set["retrieval"]["candidate_pool_ledger"]["sha256"] = quality_gate.sha256(
            self.run_dir / "candidate-pool-ledger.json"
        )
        write_json(self.run_dir / "reference-set.json", reference_set)

        quality = quality_gate.load_json(self.run_dir / "quality-result.json")
        quality["reference_comparisons"] = [
            comparison for comparison in quality["reference_comparisons"]
            if comparison["reference_id"] in frontier_ids
        ]
        quality["structural_concerns"] = []
        write_json(self.run_dir / "quality-result.json", quality)

    def _build_terminal_v12(self, status: str = "no_eligible_reference") -> None:
        self._build_retrieved_v12(
            ["candidate"],
            roles=[["calibration_anchor"]],
            bands=["boundary"],
            band_provenances=["independent_judge"],
        )
        ledger = quality_gate.load_json(self.run_dir / "candidate-pool-ledger.json")
        for entry in ledger["entries"]:
            entry["included"] = False
            entry["decision_reason"] = "hard-incomparable result"
        write_json(self.run_dir / "candidate-pool-ledger.json", ledger)
        reference_set = quality_gate.load_json(self.run_dir / "reference-set.json")
        reference_set["mode"] = "auto"
        reference_set["retrieval"]["status"] = status
        if status == "failed":
            reference_set["retrieval"]["failure_reason"] = "provider failed after bounded attempts"
        reference_set["references"] = []
        reference_set["retrieval"]["candidate_pool_ledger"]["sha256"] = quality_gate.sha256(
            self.run_dir / "candidate-pool-ledger.json"
        )
        write_json(self.run_dir / "reference-set.json", reference_set)
        quality = quality_gate.load_json(self.run_dir / "quality-result.json")
        quality["reference_comparisons"] = []
        write_json(self.run_dir / "quality-result.json", quality)

    def test_init_requests_automatic_retrieval(self) -> None:
        mode = quality_gate.determine_reference_mode(self.run_dir)
        self.assertEqual(mode["reference_mode"], "retrieve_required")
        self.assertTrue(mode["auto_retrieve"])

    def test_human_reference_remains_formally_accepted(self) -> None:
        self._human_reference("human")
        quality = quality_gate.load_json(self.run_dir / "quality-result.json")
        quality["calibration"] = {"human_anchored": True, "leniency": 0.0, "agreement": {"spearman": 0.9}}
        write_json(self.run_dir / "quality-result.json", quality)
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["reference_mode"], "human_graded")

    def test_legacy_model_reference_still_routes_to_needs_human(self) -> None:
        self.config.pop("reference_fallback")
        write_json(self.run_dir / "gate-config.json", self.config)
        self._human_reference("model")
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "needs_human")
        self.assertEqual(result["reference_mode"], "legacy_directional")

    def test_retrieved_frontier_can_pass_provisionally(self) -> None:
        self._build_retrieved(["candidate"])
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "provisional_outperforms_retrieved")
        self.assertTrue(result["comparison_pass"])

    def test_retrieved_shortfall_is_provisional(self) -> None:
        self._build_retrieved(["reference"])
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "provisional_shortfall")

    def test_all_frontier_references_are_conjoined(self) -> None:
        self._build_retrieved(["candidate", "reference"])
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "provisional_shortfall")
        self.assertEqual([item["result"] for item in result["comparisons"]], ["pass", "shortfall"])

    def test_order_flip_needs_human(self) -> None:
        self._build_retrieved(["inconsistent"])
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "needs_human")
        self.assertFalse(result["order_consistent"])

    def test_ungraded_reference_needs_human(self) -> None:
        self._build_retrieved(["candidate"], tier="retrieved_ungraded")
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "needs_human")

    def test_structural_failure_blocks_retrieved_mode(self) -> None:
        self._write_core(candidate_score=4.6, structural_pass=False)
        self._build_retrieved(["candidate"])
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "blocked")

    def test_no_eligible_reference_still_runs_diagnostic_gate(self) -> None:
        self._build_terminal_v12()
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "needs_human")
        self.assertEqual(result["reference_mode"], "reference_free_diagnostic")

    def test_missing_dimension_evidence_is_invalid(self) -> None:
        self._build_retrieved(["candidate"])
        reference_set = quality_gate.load_json(self.run_dir / "reference-set.json")
        reference_set["references"][0]["scoring"]["dimensions"][self.dimensions[0]]["evidence_locators"] = []
        write_json(self.run_dir / "reference-set.json", reference_set)
        with self.assertRaisesRegex(ValueError, "evidence_locators"):
            quality_gate.evaluate(self.run_dir)

    def test_candidate_pool_hash_drift_is_invalid(self) -> None:
        self._build_retrieved(["candidate"])
        ledger = quality_gate.load_json(self.run_dir / "candidate-pool-ledger.json")
        ledger["drift"] = True
        write_json(self.run_dir / "candidate-pool-ledger.json", ledger)
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            quality_gate.evaluate(self.run_dir)

    def test_candidate_scoring_lane_must_match_policy(self) -> None:
        self._build_retrieved(["candidate"])
        quality = quality_gate.load_json(self.run_dir / "quality-result.json")
        quality["scoring_lane"] = "other-lane"
        write_json(self.run_dir / "quality-result.json", quality)
        with self.assertRaisesRegex(ValueError, "scoring_lane"):
            quality_gate.evaluate(self.run_dir)

    def test_multiple_scoring_lanes_are_rejected_in_schema_1_1(self) -> None:
        self._build_retrieved(["candidate"])
        reference_set = quality_gate.load_json(self.run_dir / "reference-set.json")
        reference_set["evaluation_policy"]["scoring_lanes"].append("second-lane")
        write_json(self.run_dir / "reference-set.json", reference_set)
        with self.assertRaisesRegex(ValueError, "exactly one scoring lane"):
            quality_gate.evaluate(self.run_dir)

    def test_unresolved_bias_audit_needs_human(self) -> None:
        self._build_retrieved(["candidate"])
        quality = quality_gate.load_json(self.run_dir / "quality-result.json")
        quality["reference_comparisons"][0]["bias_audit"]["suspected_confounds"] = ["verbosity"]
        quality["reference_comparisons"][0]["bias_audit"]["unresolved"] = True
        write_json(self.run_dir / "quality-result.json", quality)
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "needs_human")

    def test_task_fingerprint_must_be_safe_for_outbound_search(self) -> None:
        self._build_retrieved(["candidate"])
        reference_set = quality_gate.load_json(self.run_dir / "reference-set.json")
        reference_set["task_fingerprint"]["contains_private_data"] = True
        write_json(self.run_dir / "reference-set.json", reference_set)
        with self.assertRaisesRegex(ValueError, "contains_private_data"):
            quality_gate.evaluate(self.run_dir)

    def test_included_snapshot_must_be_inert(self) -> None:
        self._build_retrieved(["candidate"])
        ledger = quality_gate.load_json(self.run_dir / "candidate-pool-ledger.json")
        ledger["entries"][0]["active_content_neutralized"] = False
        write_json(self.run_dir / "candidate-pool-ledger.json", ledger)
        reference_set = quality_gate.load_json(self.run_dir / "reference-set.json")
        reference_set["retrieval"]["candidate_pool_ledger"]["sha256"] = quality_gate.sha256(
            self.run_dir / "candidate-pool-ledger.json"
        )
        write_json(self.run_dir / "reference-set.json", reference_set)
        with self.assertRaisesRegex(ValueError, "active content"):
            quality_gate.evaluate(self.run_dir)

    def test_snapshot_content_drift_is_invalid(self) -> None:
        self._build_retrieved(["candidate"])
        snapshot = self.run_dir / "snapshots" / "ref-001.txt"
        snapshot.write_text("changed reference\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "snapshot hash mismatch"):
            quality_gate.evaluate(self.run_dir)

    def test_hard_incomparable_reference_needs_human(self) -> None:
        self._build_retrieved(["candidate"])
        reference_set = quality_gate.load_json(self.run_dir / "reference-set.json")
        reference_set["references"][0]["comparability"] = {
            "hard_pass": False,
            "reasons": ["different artifact type"],
        }
        write_json(self.run_dir / "reference-set.json", reference_set)
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "needs_human")

    def test_model_adapted_reference_cannot_provisionally_pass(self) -> None:
        self._build_retrieved(["candidate"], tier="model_adapted")
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "needs_human")

    def test_pool_entry_requires_decision_reason(self) -> None:
        self._build_retrieved(["candidate"])
        ledger = quality_gate.load_json(self.run_dir / "candidate-pool-ledger.json")
        ledger["entries"][0]["decision_reason"] = ""
        write_json(self.run_dir / "candidate-pool-ledger.json", ledger)
        reference_set = quality_gate.load_json(self.run_dir / "reference-set.json")
        reference_set["retrieval"]["candidate_pool_ledger"]["sha256"] = quality_gate.sha256(
            self.run_dir / "candidate-pool-ledger.json"
        )
        write_json(self.run_dir / "reference-set.json", reference_set)
        with self.assertRaisesRegex(ValueError, "decision_reason"):
            quality_gate.evaluate(self.run_dir)

    def test_v12_verified_high_frontier_can_pass_provisionally(self) -> None:
        self._build_retrieved_v12(["candidate"])
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["schema_version"], "1.2")
        self.assertEqual(result["status"], "provisional_outperforms_retrieved")
        self.assertTrue(result["absolute_floor_pass"])
        self.assertEqual(result["frontier_reference_ids"], ["ref-001"])

    def test_v12_anchor_only_panel_is_diagnostic(self) -> None:
        self._build_retrieved_v12(
            ["candidate"],
            roles=[["calibration_anchor"]],
            bands=["boundary"],
            band_provenances=["independent_judge"],
        )
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "anchored_diagnostic")
        self.assertEqual(quality_gate.result_exit_code(result["status"]), 6)
        self.assertEqual(result["frontier_reference_ids"], [])

    def test_v12_low_anchor_cannot_lower_absolute_floor(self) -> None:
        self._write_core(candidate_score=3.5)
        self._build_retrieved_v12(
            ["candidate"],
            roles=[["calibration_anchor"]],
            bands=["low"],
            band_provenances=["independent_judge"],
            reference_scores=[2.0],
        )
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "provisional_shortfall")
        self.assertEqual(result["provisional_reason"], "absolute_quality_floor_not_met")
        self.assertFalse(result["absolute_floor_pass"])

    def test_v12_few_shot_panel_tracks_low_boundary_high(self) -> None:
        self._build_retrieved_v12(
            ["candidate", "candidate", "candidate"],
            roles=[["calibration_anchor"], ["calibration_anchor"], ["calibration_anchor"]],
            bands=["low", "boundary", "high"],
            band_provenances=["human", "independent_judge", "objective_metric"],
            reference_scores=[2.0, 3.4, 4.4],
        )
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "anchored_diagnostic")
        self.assertTrue(result["anchor_panel"]["coverage_complete"])
        self.assertTrue(result["anchor_panel"]["order_consistent"])

    def test_v12_self_labeled_high_cannot_gate_frontier(self) -> None:
        self._build_retrieved_v12(
            ["candidate"],
            band_provenances=["self_labeled"],
        )
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "needs_human")
        self.assertIn("challenge_frontier_self_labeled:ref-001", result["reasons"])

    def test_v12_nonmonotonic_anchor_panel_needs_human(self) -> None:
        self._build_retrieved_v12(
            ["candidate", "candidate", "candidate"],
            roles=[["calibration_anchor"], ["calibration_anchor"], ["calibration_anchor"]],
            bands=["low", "boundary", "high"],
            band_provenances=["human", "human", "human"],
            reference_scores=[4.2, 3.5, 4.0],
        )
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "needs_human")
        self.assertIn("anchor_panel_non_monotonic", result["reasons"])

    def test_v12_retrieved_only_dimension_cannot_be_gating(self) -> None:
        self._build_retrieved_v12(["candidate"])
        rubric = quality_gate.load_json(self.run_dir / "rubric.json")
        rubric["dimensions"][self.dimensions[0]]["origin"] = "retrieved_example"
        write_json(self.run_dir / "rubric.json", rubric)
        reference_set = quality_gate.load_json(self.run_dir / "reference-set.json")
        rubric_hash = quality_gate.sha256(self.run_dir / "rubric.json")
        reference_set["evaluation_policy"]["rubric_sha256"] = rubric_hash
        for reference in reference_set["references"]:
            reference["scoring"]["rubric_sha256"] = rubric_hash
        write_json(self.run_dir / "reference-set.json", reference_set)
        with self.assertRaisesRegex(ValueError, "unsupported origin"):
            quality_gate.evaluate(self.run_dir)

    def test_v12_structural_overlap_dimension_is_rejected(self) -> None:
        self._build_retrieved_v12(["candidate"])
        rubric = quality_gate.load_json(self.run_dir / "rubric.json")
        rubric["dimensions"][self.dimensions[0]]["structural_overlap_check"] = "failed"
        write_json(self.run_dir / "rubric.json", rubric)
        reference_set = quality_gate.load_json(self.run_dir / "reference-set.json")
        rubric_hash = quality_gate.sha256(self.run_dir / "rubric.json")
        reference_set["evaluation_policy"]["rubric_sha256"] = rubric_hash
        for reference in reference_set["references"]:
            reference["scoring"]["rubric_sha256"] = rubric_hash
        write_json(self.run_dir / "reference-set.json", reference_set)
        with self.assertRaisesRegex(ValueError, "overlaps the structural lane"):
            quality_gate.evaluate(self.run_dir)

    def test_v12_scale_endpoints_are_required(self) -> None:
        self._build_retrieved_v12(["candidate"])
        rubric = quality_gate.load_json(self.run_dir / "rubric.json")
        rubric["dimensions"][self.dimensions[0]]["scale_anchors"].pop("5")
        write_json(self.run_dir / "rubric.json", rubric)
        reference_set = quality_gate.load_json(self.run_dir / "reference-set.json")
        rubric_hash = quality_gate.sha256(self.run_dir / "rubric.json")
        reference_set["evaluation_policy"]["rubric_sha256"] = rubric_hash
        for reference in reference_set["references"]:
            reference["scoring"]["rubric_sha256"] = rubric_hash
        write_json(self.run_dir / "reference-set.json", reference_set)
        with self.assertRaisesRegex(ValueError, "scale anchors"):
            quality_gate.evaluate(self.run_dir)

    def test_v12_structural_concerns_are_handed_off_not_double_scored(self) -> None:
        self._build_retrieved_v12(["candidate"])
        quality = quality_gate.load_json(self.run_dir / "quality-result.json")
        quality["structural_concerns"] = [{"claim": "schema concern", "locator": "artifact.txt"}]
        write_json(self.run_dir / "quality-result.json", quality)
        result = quality_gate.evaluate(self.run_dir)
        self.assertEqual(result["status"], "provisional_outperforms_retrieved")

    def test_v12_terminal_retrieval_detects_ledger_drift(self) -> None:
        self._build_terminal_v12()
        ledger = quality_gate.load_json(self.run_dir / "candidate-pool-ledger.json")
        ledger["drift"] = True
        write_json(self.run_dir / "candidate-pool-ledger.json", ledger)
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            quality_gate.evaluate(self.run_dir)

    def test_v12_reference_free_rejects_stale_comparisons(self) -> None:
        self._build_terminal_v12()
        quality = quality_gate.load_json(self.run_dir / "quality-result.json")
        quality["reference_comparisons"] = [{"reference_id": "stale"}]
        write_json(self.run_dir / "quality-result.json", quality)
        with self.assertRaisesRegex(ValueError, "empty reference_comparisons"):
            quality_gate.evaluate(self.run_dir)


if __name__ == "__main__":
    unittest.main(verbosity=2)
