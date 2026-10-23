"""Native Ansible HTTP fixture tests. Requires ansible-core and PyYAML.

Run: python3 -m unittest discover -s automation/ansible/tests -v
"""
import http.server
import pathlib
import re
import subprocess
import sys
import tempfile
import threading
import unittest

import jinja2
import yaml

ROLE = pathlib.Path(__file__).resolve().parents[1] / "roles/ocp4_workload_konflux_tssc_cluster"


class ProbeTests(unittest.TestCase):
    def probe(self, responses, retries=0, push_result=None):
        probe_file = ROLE / "tasks/probe-quay-registry.yml"
        self.assertTrue(probe_file.exists(), "Native Ansible probe is missing")
        tasks = yaml.safe_load(probe_file.read_text())
        seen = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append(self.path)
                status, headers = responses[min(len(seen) - 1, len(responses) - 1)]
                self.send_response(status)
                for key, value in headers.items():
                    self.send_header(key, value)
                self.send_header("Set-Cookie", "session=SENSITIVE_SENTINEL")
                self.end_headers()
                self.wfile.write(b"SENSITIVE_SENTINEL response body")

            def log_message(self, *args):
                pass

        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                # Replace only the destination; execute the actual production tasks.
                tasks[0]["ansible.builtin.uri"]["url"] = f"http://127.0.0.1:{server.server_port}/v2/"
                play = [{"hosts": "localhost", "gather_facts": False, "vars": {
                    "ansible_python_interpreter": sys.executable,
                    "quay_registry_probe_retries": retries,
                    "quay_registry_probe_delay": 0,
                }, "tasks": tasks}]
                if push_result is not None:
                    push_tasks = yaml.safe_load((ROLE / "tasks/push-unsigned-sample-image.yml").read_text())
                    play[0]["vars"].update(r_push_image=push_result, quay_registry_probe_required=False)
                    tasks.insert(0, next(t for t in push_tasks if t["name"] == "Record whether the unsigned image push failed"))
                    tasks.append(next(t for t in push_tasks if t["name"] == "Report sanitized unsigned image push failure"))
                with tempfile.TemporaryDirectory() as directory:
                    path = pathlib.Path(directory) / "probe.yml"
                    path.write_text(yaml.safe_dump(play))
                    result = subprocess.run(
                        [sys.executable, "-m", "ansible.cli.playbook", "-i", "localhost,", "-c", "local", str(path)],
                        capture_output=True, text=True, timeout=60,
                    )
            finally:
                server.shutdown()
                thread.join()
        self.assertNotIn("SENSITIVE_SENTINEL", result.stdout + result.stderr)
        return result, seen

    def test_registry_auth_challenge_is_ready(self):
        result, seen = self.probe([(401, {"Docker-Distribution-Api-Version": "registry/2.0"})])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(seen, ["/v2/"])

    def test_html_success_is_not_registry_readiness(self):
        result, _ = self.probe([(200, {})])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("registry_api=False", result.stdout)

    def test_transient_unavailable_then_ready(self):
        result, seen = self.probe([(503, {}), (200, {"Docker-Distribution-Api-Version": "registry/2.0"})], 1)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(seen), 2)

    def test_405_is_not_retried(self):
        result, seen = self.probe([(405, {})], 2)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(seen), 1)
        self.assertIn("http_status=405", result.stdout)

    def test_redirect_is_not_followed_or_disclosed(self):
        result, seen = self.probe([(302, {"Location": "https://example.test/?token=SENSITIVE_SENTINEL"})], 2)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(seen), 1)
        self.assertIn("redirect=True", result.stdout)
        self.assertNotIn("example.test", result.stdout)

    def test_transient_retries_are_bounded(self):
        result, seen = self.probe([(503, {})], 1)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(seen), 2)

    def test_route_selects_http_backend(self):
        env = jinja2.Environment(undefined=jinja2.StrictUndefined)
        env.filters["regex_replace"] = lambda value, pattern, replacement: re.sub(pattern, replacement, value)
        template = env.from_string((ROLE / "templates/route-quay-showroom.yaml.j2").read_text())
        for api in ["https://api.ocp.example.test:6443", "https://api.cluster.example.test:6443"]:
            route = yaml.safe_load(template.render(openshift_api_url=api))
            self.assertEqual(route["spec"].get("port"), {"targetPort": "http"})
            self.assertEqual(route["spec"]["to"]["name"], "quay-quay-app")

    def test_successful_probe_does_not_mask_push_failure(self):
        result, seen = self.probe(
            [(200, {"Docker-Distribution-Api-Version": "registry/2.0"})],
            push_result={"rc": 1, "stderr": "StatusCode: 405, SENSITIVE_SENTINEL"},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(seen), 1)
        self.assertIn("Unsigned image push failed", result.stdout)
        self.assertIn("Registry HTTP status from skopeo: 405", result.stdout)


if __name__ == "__main__":
    unittest.main()
