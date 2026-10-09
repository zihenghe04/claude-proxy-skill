import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/claude-proxy-optimize/scripts/proxy_tool.py'
spec = importlib.util.spec_from_file_location('proxy_tool', SCRIPT)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class FakeController:
    def __init__(self):
        self.now = 'Original'
        self.selections = []

    def group(self, name):
        return {'type': 'Selector', 'now': self.now, 'all': ['Original', 'Candidate']}

    def select(self, group, node):
        self.now = node
        self.selections.append(node)


class ToolsTests(unittest.TestCase):
    def test_summary_never_exports_credentials_or_browsing_metadata(self):
        config = {'secret': 'private-api-value', 'proxies': [{'name': 'Private Node',
                   'password': 'private-node-value', 'uuid': 'private-identifier'}],
                  'dns': {'nameserver': ['8.8.8.8'], 'nameserver-policy': {'private.example': 'system'}},
                  'subscription_url': 'https://private.example/subscription'}
        encoded = json.dumps(tool.inspect_config(config))
        for private in ['private-api-value', 'private-node-value', 'Private Node',
                        'private-identifier', 'private.example']:
            self.assertNotIn(private, encoded)

    def test_plan_is_scoped_and_leaves_input_unchanged(self):
        config = {'proxies': [{'name': 'Candidate', 'password': 'private-node-value'}],
                  'rules': ['DOMAIN-SUFFIX,internal.example,DIRECT'],
                  'dns': {'direct-nameserver': ['system']}}
        before = json.dumps(config)
        overlays = tool.plan(config, 'Candidate')
        self.assertEqual(before, json.dumps(config))
        self.assertEqual(len(overlays['rules.yaml']['prepend']), len(tool.CORE))
        self.assertNotIn('nameserver', overlays['dns-policy.yaml']['dns'])
        self.assertNotIn('direct-nameserver', overlays['dns-policy.yaml']['dns'])
        self.assertNotIn('private-node-value', json.dumps(overlays))
        self.assertNotIn('sentry.io', json.dumps(overlays))

    def test_reject_group_collision_and_rule_injection(self):
        config = {'proxies': [{'name': 'Candidate'}], 'proxy-groups': [{'name': 'Claude'}]}
        with self.assertRaises(ValueError):
            tool.plan(config, 'Candidate')
        with self.assertRaises(ValueError):
            tool.plan({'proxies': [{'name': 'Candidate'}]}, 'Candidate', 'A,B')

    def test_probe_restores_after_interrupt(self):
        controller = FakeController()
        def interrupted(proxy, timeout):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            tool.probe(controller, 'Test', ['Candidate'], 'http://127.0.0.1:7890', trace_fn=interrupted)
        self.assertEqual(controller.now, 'Original')
        self.assertEqual(controller.selections, ['Candidate', 'Original'])

    def test_probe_redacts_exit_and_skips_risk_by_default(self):
        controller = FakeController()
        def traced(proxy, timeout):
            return {'ip': '192.0.2.10', 'country': 'US', 'request_seconds': 0.5}
        def forbidden(*args):
            self.fail('Risk endpoint must be opt-in')
        result = tool.probe(controller, 'Test', ['Candidate'], 'http://127.0.0.1:7890',
                            trace_fn=traced, risk_fn=forbidden)
        encoded = json.dumps(result)
        self.assertNotIn('192.0.2.10', encoded)
        self.assertNotIn('node', result['candidates'][0])
        self.assertTrue(result['restored'])
        self.assertEqual(result['candidates'][0]['ip_version'], 4)

    def test_probe_reports_failure_without_leaking_exception(self):
        def failure(*args):
            raise OSError('private credential details')
        result = tool.probe(FakeController(), 'Test', ['Candidate'], 'http://localhost:7890', trace_fn=failure)
        self.assertFalse(result['candidates'][0]['ok'])
        self.assertNotIn('private credential details', json.dumps(result))

    def test_disallow_remote_and_credential_urls(self):
        for url in ['http://192.0.2.1:9090', 'http://user:pass@localhost:9090',
                    'http://localhost:9090/?token=example', 'https://localhost:9090']:
            with self.assertRaises(ValueError):
                tool.validate_loopback(url)

    def test_plan_cli_has_private_files_and_no_live_edit(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            config = base / 'source.yaml'
            config.write_text('proxies:\n  - name: Candidate\n')
            before = config.read_bytes()
            output = base / 'output'
            subprocess.run([sys.executable, str(SCRIPT), 'plan', '--config', str(config),
                            '--node', 'Candidate', '--output', str(output)], check=True, capture_output=True)
            self.assertEqual(config.read_bytes(), before)
            self.assertEqual(len(list(output.iterdir())), 3)
            if os.name != 'nt':
                for file in output.iterdir():
                    self.assertEqual(file.stat().st_mode & 0o777, 0o600)

    def test_install_refuses_overwrite_and_preserves_files(self):
        with tempfile.TemporaryDirectory() as temp:
            command = [sys.executable, str(ROOT / 'install.py'), '--dest', temp]
            subprocess.run(command, check=True, capture_output=True)
            installed = Path(temp) / 'claude-proxy-optimize' / 'SKILL.md'
            before = installed.read_bytes()
            result = subprocess.run(command, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(installed.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
