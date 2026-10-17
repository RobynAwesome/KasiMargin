import copy
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator, ValidationError
from kasimargin.workflow import decision

ROOT = Path(__file__).resolve().parents[1]


class Contracts(unittest.TestCase):
    def validator(self, name):
        schema = json.loads((ROOT / "docs" / name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        return Draft202012Validator(schema)

    def test_four_contracts_cover_all_synthetic_inputs_and_outputs(self):
        validators = {name:self.validator(name) for name in ("input.schema.json", "input-v2.schema.json", "summary.schema.json", "model-selection.schema.json")}
        paths = [ROOT / "fixtures" / f"{n:02}.json" for n in range(1,7)] + [ROOT / "fixtures/itemized/01.json"]
        for path in paths:
            with self.subTest(path=path.name):
                request = json.loads(path.read_text(encoding="utf-8"))["input"]
                validators["input-v2.schema.json" if "schema_version" in request else "input.schema.json"].validate(request)
                result = decision(request)
                validators["summary.schema.json"].validate(result["summary"])
                validators["model-selection.schema.json"].validate(result["selection"])

    def test_summary_contract_preserves_unknown_and_rejects_conflicting_cash_claims(self):
        validator = self.validator("summary.schema.json")
        request = json.loads((ROOT / "fixtures/04.json").read_text(encoding="utf-8"))["input"]
        summary = decision(request)["summary"]
        forged = copy.deepcopy(summary); forged["cash_headroom_cents"] = 0
        with self.assertRaises(ValidationError): validator.validate(forged)
        request = json.loads((ROOT / "fixtures/01.json").read_text(encoding="utf-8"))["input"]
        forged = decision(request)["summary"]; forged["protected_cash_deficit_cents"] = 1
        with self.assertRaises(ValidationError): validator.validate(forged)

    def test_negative_margin_is_independent_of_confirmed_cash(self):
        request = json.loads((ROOT / "fixtures/01.json").read_text(encoding="utf-8"))["input"]
        request["performance"].update(recorded_sales_cents=100, attributable_costs_cents=200)
        summary = decision(request)["summary"]
        self.validator("summary.schema.json").validate(summary)
        self.assertEqual(summary["operating_margin_cents"], -100)
        self.assertEqual(summary["cash_headroom_cents"], 40000)
