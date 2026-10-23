"""Exercise the pod-side probe against a local HTTP server (no cluster needed)."""
import http.server
import pathlib
import subprocess
import threading
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "roles/ocp4_workload_konflux_tssc_cluster/files/quay-registry-probe.sh"


class ProbeTests(unittest.TestCase):
    def probe(self, responses, attempts=1):
        seen = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append(self.path)
                status, headers = responses[min(len(seen) - 1, len(responses) - 1)]
                self.send_response(status)
                for key, value in headers.items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(b"sensitive response body must not be logged")

            def log_message(self, *args):
                pass

        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                result = subprocess.run(
                    ["bash", str(SCRIPT), f"http://127.0.0.1:{server.server_port}/v2/", str(attempts), "0"],
                    capture_output=True, text=True, timeout=10,
                )
            finally:
                server.shutdown()
                thread.join()
        self.assertNotIn("sensitive", result.stdout + result.stderr)
        return result, seen

    def test_registry_auth_challenge_is_ready(self):
        result, seen = self.probe([(401, {"Docker-Distribution-Api-Version": "registry/2.0"})])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(seen, ["/v2/"])

    def test_html_success_is_not_registry_readiness(self):
        result, _ = self.probe([(200, {})])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("registry_api=false", result.stdout)

    def test_transient_unavailable_then_ready(self):
        result, seen = self.probe([(503, {}), (200, {"Docker-Distribution-Api-Version": "registry/2.0"})], 2)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(seen), 2)

    def test_405_is_not_retried(self):
        result, seen = self.probe([(405, {})], 3)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(seen), 1)
        self.assertIn("http_status=405", result.stdout)

    def test_redirect_is_not_followed_or_disclosed(self):
        result, seen = self.probe([(302, {"Location": "https://example.test/?token=sensitive"})], 3)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(seen), 1)
        self.assertIn("redirect=true", result.stdout)
        self.assertNotIn("example.test", result.stdout)

    def test_transient_retries_are_bounded(self):
        result, seen = self.probe([(503, {})], 2)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(seen), 2)


if __name__ == "__main__":
    unittest.main()
