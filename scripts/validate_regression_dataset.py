from __future__ import annotations
import importlib.util,json
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/regression-dataset-policy.json").read_text());dataset_path=ROOT/"data/synthetic/regression-cases.json";manifest_path=ROOT/"data/synthetic/regression-replay-manifest.json";data=json.loads(dataset_path.read_text());manifest=json.loads(manifest_path.read_text())
 spec=importlib.util.spec_from_file_location("generator",ROOT/"data/synthetic/generate_regression_dataset.py");assert spec and spec.loader;generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
 if dataset_path.read_bytes()!=generator.canonical_dataset_bytes() or manifest_path.read_bytes()!=generator.canonical_manifest_bytes():errors.append("regression corpus or manifest is not deterministic")
 cases=data.get("cases",[]);required=set(policy["required_fields"])
 if len(cases)!=policy["exact_case_count"] or data.get("case_count")!=len(cases):errors.append("case count is not exactly 500")
 if any(required-set(c) for c in cases):errors.append("regression fields are incomplete")
 if len({c.get("regression_id") for c in cases})!=len(cases):errors.append("regression ids are not unique")
 if Counter(c["domain"] for c in cases)!=Counter(policy["domain_case_counts"]):errors.append("domain balance is invalid")
 if Counter(c["scenario_class"] for c in cases)!=Counter(policy["scenario_class_counts"]):errors.append("scenario class balance is invalid")
 grouped=defaultdict(set)
 for case in cases:grouped[case["source_case_id"]].add(case["split"])
 if any(len(splits)!=1 for splits in grouped.values()):errors.append("source case leaked across splits")
 if set(c["split"] for c in cases)!=set(policy["splits"]):errors.append("split coverage is incomplete")
 if len({c["endpoint_id"] for c in cases})!=10 or len({c["incident_id"] for c in cases})!=44:errors.append("endpoint or incident taxonomy coverage is incomplete")
 for case in cases:
  expected=case.get("expected",{});refs=case.get("artifact_refs",{});input_data=case.get("input",{})
  if not input_data.get("symptoms") or not input_data.get("diagnostic_evidence") or not expected.get("root_cause") or not expected.get("rollback") or not expected.get("verification"):errors.append("input or expected outcome is incomplete");break
  if any(not refs.get(key) for key in ("conversation_id","telemetry_pack_id","authorization_scenario_id","remediation_scenario_id")):errors.append("artifact lineage is incomplete");break
 if manifest.get("dataset_digest")!=data.get("dataset_digest") or manifest.get("case_count")!=len(cases):errors.append("replay manifest does not bind dataset")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("five-hundred-case regression dataset validation passed")
