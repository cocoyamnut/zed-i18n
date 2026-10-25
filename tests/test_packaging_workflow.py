import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


class PackagingWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = Path('.github/workflows/i18n-update-packaging.yml').read_text()

    def test_packaging_requires_owned_repository_and_configured_token(self) -> None:
        job = self.workflow.split('  update-packaging:\n', 1)[1]
        condition = re.search(r'    if: >-\n(.*?)    runs-on:', job, re.S).group(1)
        self.assertIn("github.repository == 'cocoyamnut/zed-i18n' &&", condition)
        self.assertIn("needs.packaging-access.outputs.enabled == 'true' &&", condition)
        self.assertIn("github.event_name == 'workflow_dispatch' ||", condition)
        self.assertIn('github.event.release.prerelease == false', condition)
        self.assertEqual(condition.count('('), condition.count(')'))
        self.assertIn('needs: packaging-access', job)
        self.assertNotIn('LI-NA', self.workflow)
        self.assertNotIn('li-na', self.workflow)
        self.assertIn('HOMEBREW_REPOSITORY: cocoyamnut/homebrew-zed-i18n', self.workflow)
        self.assertIn('SCOOP_REPOSITORY: cocoyamnut/scoop-zed-i18n', self.workflow)
        self.assertIn('tap_name="${tap_owner}/${tap_repo#homebrew-}"', self.workflow)

    def test_token_check_skips_safely_and_never_outputs_token(self) -> None:
        preflight = self.workflow.split('  packaging-access:\n', 1)[1].split('  update-packaging:\n', 1)[0]
        script = preflight.split('        run: |\n', 1)[1]
        script = '\n'.join(line[10:] for line in script.splitlines())
        for token, enabled in (('', 'false'), ('test-only-not-a-real-secret', 'true')):
            with self.subTest(configured=bool(token)), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / 'output'
                result = subprocess.run(
                    ['bash', '-euo', 'pipefail', '-c', script],
                    env={**os.environ, 'PACKAGING_REPOS_TOKEN': token, 'GITHUB_OUTPUT': str(output)},
                    capture_output=True, text=True, check=True,
                )
                self.assertEqual(output.read_text(), f'enabled={enabled}\n')
                if token:
                    self.assertNotIn(token, result.stdout + result.stderr + output.read_text())
                else:
                    self.assertIn('Packaging skipped', result.stdout)

    def test_metadata_is_validated_before_packaging_repositories_are_accessed(self) -> None:
        self.assertLess(self.workflow.index('- name: Validate release metadata'),
                        self.workflow.index('- name: Checkout Homebrew tap'))
        self.assertIn('manifest repository mismatch', self.workflow)
        self.assertIn('release asset missing from published release', self.workflow)
        self.assertIn('checksum mismatch between manifest.json and SHA256SUMS.txt', self.workflow)

    def test_release_dispatches_owned_packaging_only_after_asset_validation_and_publication(self) -> None:
        workflow = Path('.github/workflows/i18n-release.yml').read_text()
        self.assertEqual(workflow.count("--installed-identity zed-stable"), 1)
        metadata = workflow.split("ci_release metadata", 1)[1].split("      - name:", 1)[0]
        self.assertIn("--installed-identity zed-stable", metadata)
        step = workflow.split('      - name: Update packaging\n', 1)[1]
        self.assertIn("        if: github.repository == 'cocoyamnut/zed-i18n'\n", step)
        self.assertIn('gh workflow run i18n-update-packaging.yml', step)
        self.assertLess(workflow.index('- name: Validate release assets'), workflow.index('- name: Publish release'))
        self.assertLess(workflow.index('- name: Publish release'), workflow.index('- name: Update packaging\n'))


if __name__ == '__main__':
    unittest.main()
