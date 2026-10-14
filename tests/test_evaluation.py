import unittest

from scripts.evaluate_local_gemma import validate_resume_prefix


class ResumeBoundary(unittest.TestCase):
    def rows(self, fixture):
        return [{"fixture_id": fixture, "pass": name, "output_admitted": True,
                 "inference": {"digest": "same-model"}}
                for name in ("cold", "warm-1", "warm-2")]

    def test_completed_scenarios_can_resume_without_replacing_evidence(self):
        rows = self.rows("01") + self.rows("02")
        before = repr(rows)
        validate_resume_prefix(rows, ["01", "02", "03"], 2, "same-model")
        self.assertEqual(repr(rows), before)

    def test_partial_reordered_repeated_or_extra_scenarios_are_rejected(self):
        cases = [self.rows("01")[:2], self.rows("02"),
                 self.rows("01") + self.rows("01"),
                 self.rows("01") + self.rows("02") + self.rows("03")]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                validate_resume_prefix(rows, ["01", "02"], 2, "same-model")

    def test_digest_drift_cannot_blend_model_runs(self):
        with self.assertRaises(ValueError):
            validate_resume_prefix(self.rows("01"), ["01", "02"], 2, "changed-model")
