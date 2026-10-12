import json
from pathlib import Path
import tempfile
import unittest
from kasimargin.engine import ContractError
from kasimargin.jsonio import dumps, loads
from kasimargin.receipts import save, verify, digest
from kasimargin.workflow import decision

ROOT = Path(__file__).resolve().parents[1]


class Receipts(unittest.TestCase):
    def test_save_and_replay_without_model_or_overwrite(self):
        request = loads((ROOT / "fixtures/itemized/01.json").read_text())["input"]
        result = decision(request)
        with tempfile.TemporaryDirectory() as directory:
            first = save(request, result, "SYNTHETIC", directory)
            second = save(request, result, "SYNTHETIC", directory)
            self.assertNotEqual(first, second)
            self.assertEqual(verify(first)["status"], "REPRODUCED")
            self.assertEqual(verify(first)["human_review"], "NOT_RECORDED")

    def test_modified_amount_or_forged_recalculation_rejected(self):
        request = loads((ROOT / "fixtures/01.json").read_text())["input"]
        with tempfile.TemporaryDirectory() as directory:
            path = save(request, decision(request), "SYNTHETIC", directory)
            envelope = loads(path.read_text())
            envelope["payload"]["result"]["summary"]["cash_headroom_cents"] = 99999
            path.write_text(dumps(envelope))
            with self.assertRaises(ContractError): verify(path)
            envelope["sha256"] = digest(envelope["payload"])
            path.write_text(dumps(envelope))
            with self.assertRaises(ContractError): verify(path)

    def test_invalid_evidence_class_and_altered_explanation_rejected(self):
        request = loads((ROOT / "fixtures/01.json").read_text())["input"]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ContractError): save(request, decision(request), "BANK_VERIFIED", directory)
            result = decision(request); result["explanation"] = "Spend everything."
            with self.assertRaises(ContractError): save(request, result, "SYNTHETIC", directory)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_duplicate_keys_and_nonstandard_numbers_rejected(self):
        for value in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.subTest(value=value):
                with self.assertRaises(ContractError): loads(value)
