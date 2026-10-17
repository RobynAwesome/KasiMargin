import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from kasimargin.kpgs import LocalKpgs, ACK, ROOT


class ContextRuntime(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        (self.root / "scripts").mkdir()
        (self.root / "scripts/kc_kpgs_governance.py").write_text("# synthetic runtime fixture", encoding="utf-8")

    def tearDown(self):
        self.directory.cleanup()

    def valid(self):
        return {"schema":"kpgs_hood_entry_assertion_v1","hood_ack_required":ACK,
                "entryway_source":"Schematics/synthetic-entry.json","renter_id":"kasimargin_context_adapter",
                "private_doctrine":"must not leave the bridge"}

    def test_context_connection_is_read_only_bounded_and_does_not_promote_authority(self):
        with patch("kasimargin.kpgs.subprocess.run", return_value=SimpleNamespace(returncode=0,stdout=json.dumps(self.valid()))) as run:
            runtime = LocalKpgs(self.root)
            first = runtime.probe(); second = runtime.probe()
        self.assertEqual(first["status"], "CONNECTED_READ_ONLY")
        self.assertEqual(first["financial_admission"], "NOT_ESTABLISHED")
        self.assertEqual(first["bank_verification"], "NOT_PERFORMED")
        self.assertNotIn("private_doctrine", first); self.assertEqual(first, second)
        self.assertEqual(run.call_count, 1)
        args, kwargs = run.call_args
        self.assertNotIn("--assert", args[0]); self.assertIn("-B", args[0]); self.assertIn("-I", args[0])
        self.assertLessEqual(kwargs["timeout"], 5)
        self.assertTrue(Path(kwargs["env"]["KC_LEDGER_ROOT"]).is_relative_to(ROOT))

    def test_missing_configuration_and_missing_entry_do_not_simulate_connection(self):
        self.assertEqual(LocalKpgs().probe()["status"], "NOT_CONFIGURED")
        self.assertEqual(LocalKpgs(self.root / "absent").probe()["status"], "UNAVAILABLE")

    def test_runtime_failure_timeout_and_invalid_identity_remain_unavailable(self):
        replies = [SimpleNamespace(returncode=1,stdout=""), SimpleNamespace(returncode=0,stdout="not JSON"),
                   SimpleNamespace(returncode=0,stdout=json.dumps({**self.valid(),"hood_ack_required":"wrong"})),
                   SimpleNamespace(returncode=0,stdout="x"*262145)]
        for reply in replies:
            with self.subTest(reply=reply.returncode), patch("kasimargin.kpgs.subprocess.run",return_value=reply):
                self.assertNotEqual(LocalKpgs(self.root).probe()["status"], "CONNECTED_READ_ONLY")
        with patch("kasimargin.kpgs.subprocess.run",side_effect=subprocess.TimeoutExpired("synthetic",5)):
            self.assertEqual(LocalKpgs(self.root).probe()["status"], "UNAVAILABLE")
