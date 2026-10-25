import json
import shutil
import unittest
from pathlib import Path

from tools.zed_i18n.packaging import (
    generate_homebrew_cask,
    generate_packaging_files,
    generate_scoop_manifests,
)


def release_asset(
    name: str,
    kind: str,
    locale: str,
    platform: str,
    arch: str,
    sha256: str,
) -> dict[str, object]:
    return {
        "name": name,
        "kind": kind,
        "locale": locale,
        "platform": platform,
        "arch": arch,
        "size": 123,
        "sha256": sha256,
        "download_url": f"https://github.com/LI-NA/zed-i18n/releases/download/v1.4.4-i18n.2/{name}",
    }


def sample_manifest(locales: tuple[str, ...] = ("ja-JP", "ko-KR")) -> dict[str, object]:
    assets: list[dict[str, object]] = []
    for locale in locales:
        assets.extend(
            [
                release_asset(
                    f"Zed-i18n-{locale}-macos-aarch64.dmg",
                    "app",
                    locale,
                    "macos",
                    "aarch64",
                    f"mac-arm-{locale}",
                ),
                release_asset(
                    f"Zed-i18n-{locale}-macos-x86_64.dmg",
                    "app",
                    locale,
                    "macos",
                    "x86_64",
                    f"mac-intel-{locale}",
                ),
                release_asset(
                    f"zed-i18n-{locale}-linux-aarch64.tar.gz",
                    "app",
                    locale,
                    "linux",
                    "aarch64",
                    f"linux-arm-{locale}",
                ),
                release_asset(
                    f"zed-i18n-{locale}-linux-x86_64.tar.gz",
                    "app",
                    locale,
                    "linux",
                    "x86_64",
                    f"linux-intel-{locale}",
                ),
                release_asset(
                    f"Zed-i18n-{locale}-windows-aarch64.zip",
                    "portable_app",
                    locale,
                    "windows",
                    "aarch64",
                    f"win-arm-{locale}",
                ),
                release_asset(
                    f"Zed-i18n-{locale}-windows-x86_64.zip",
                    "portable_app",
                    locale,
                    "windows",
                    "x86_64",
                    f"win-x64-{locale}",
                ),
            ]
        )
    return {
        "schema": 2,
        "installed_identity": "zed-stable",
        "zed_version": "v1.4.4",
        "i18n_revision": 2,
        "release_tag": "v1.4.4-i18n.2",
        "repository": "LI-NA/zed-i18n",
        "asset_count": len(assets),
        "assets": assets,
    }


def universal_release_asset(
    name: str,
    kind: str,
    platform: str,
    arch: str,
    sha256: str,
    locale: str | None = None,
) -> dict[str, object]:
    return {
        "name": name,
        "kind": kind,
        "locale": locale,
        "platform": platform,
        "arch": arch,
        "size": 123,
        "sha256": sha256,
        "download_url": f"https://github.com/LI-NA/zed-i18n/releases/download/v1.4.4-i18n.2/{name}",
    }


def sample_universal_manifest(
    alias_locales: tuple[str, ...] = ("ja-JP", "ko-KR"),
) -> dict[str, object]:
    universal_apps = [
        universal_release_asset("zed-i18n-linux-aarch64.tar.gz", "app", "linux", "aarch64", "lin-arm"),
        universal_release_asset("zed-i18n-linux-x86_64.tar.gz", "app", "linux", "x86_64", "lin-x64"),
        universal_release_asset("Zed-i18n-macos-aarch64.dmg", "app", "macos", "aarch64", "mac-arm"),
        universal_release_asset("Zed-i18n-macos-x86_64.dmg", "app", "macos", "x86_64", "mac-intel"),
        universal_release_asset("Zed-i18n-windows-aarch64.exe", "app", "windows", "aarch64", "win-arm"),
        universal_release_asset("Zed-i18n-windows-x86_64.exe", "app", "windows", "x86_64", "win-x64"),
    ]
    assets = [
        *universal_apps,
        universal_release_asset(
            "Zed-i18n-windows-aarch64.zip", "portable_app", "windows", "aarch64", "zip-arm"
        ),
        universal_release_asset(
            "Zed-i18n-windows-x86_64.zip", "portable_app", "windows", "x86_64", "zip-x64"
        ),
        universal_release_asset(
            "zed-i18n-linux-x86_64.deb", "deb_package", "linux", "x86_64", "deb-x64"
        ),
    ]
    for locale in alias_locales:
        for app in universal_apps:
            alias = dict(app)
            alias["locale"] = locale
            assets.append(alias)
    return {
        "schema": 2,
        "installed_identity": "zed-stable",
        "zed_version": "v1.4.4",
        "i18n_revision": 2,
        "release_tag": "v1.4.4-i18n.2",
        "repository": "LI-NA/zed-i18n",
        "asset_count": len(assets),
        "assets": assets,
    }


class PackagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path.cwd() / "tests" / ".tmp" / self._testMethodName
        shutil.rmtree(self.tmp, ignore_errors=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fork_packaging_uses_its_own_repository_everywhere(self) -> None:
        for factory in (sample_universal_manifest,):
            with self.subTest(mode=factory.__name__):
                manifest = factory()
                manifest["repository"] = "cocoyamnut/zed-i18n"
                for asset in manifest["assets"]:
                    asset["download_url"] = asset["download_url"].replace(
                        "LI-NA/zed-i18n", "cocoyamnut/zed-i18n"
                    )
                url = "https://github.com/cocoyamnut/zed-i18n"
                cask = generate_homebrew_cask(manifest)
                self.assertNotIn("LI-NA", cask)
                self.assertIn(f'homepage "{url}"', cask)
                self.assertEqual(cask.count(f'{url}/releases/download/'), 2)
                for filename, text in generate_scoop_manifests(manifest).items():
                    with self.subTest(filename=filename):
                        self.assertNotIn("LI-NA", text)
                        app = json.loads(text)
                        self.assertEqual(app["homepage"], url)
                        self.assertEqual(app["checkver"]["url"], f"{url}/releases/latest")
                        for architecture in ("64bit", "arm64"):
                            self.assertTrue(app["architecture"][architecture]["url"].startswith(
                                f"{url}/releases/download/v1.4.4-i18n.2/"
                            ))
                            self.assertTrue(app["autoupdate"]["architecture"][architecture]["url"].startswith(
                                f"{url}/releases/download/v$version/"
                            ))
                        self.assertEqual(app["autoupdate"]["hash"]["url"],
                                         f"{url}/releases/download/v$version/SHA256SUMS.txt")

    def test_packaging_requires_explicit_stable_identity_build_declaration(self) -> None:
        # This declaration gates compatibility with the new build layout; it
        # does not replace native binary/installer verification before release.
        for factory in (sample_manifest, sample_universal_manifest):
            for identity in (None, "", "zed-i18n", "Zed", True):
                manifest = factory()
                if identity is None:
                    manifest.pop("installed_identity")
                else:
                    manifest["installed_identity"] = identity
                for generator in (generate_homebrew_cask, generate_scoop_manifests):
                    with self.subTest(mode=factory.__name__, identity=identity,
                                      generator=generator.__name__):
                        with self.assertRaisesRegex(ValueError, "installed_identity.*zed-stable"):
                            generator(manifest)
                manifest_path = self.tmp / "manifest.json"
                manifest_path.parent.mkdir(parents=True, exist_ok=True)
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                cask_path = self.tmp / "out" / "zed-i18n.rb"
                bucket_path = self.tmp / "bucket"
                with self.assertRaisesRegex(ValueError, "installed_identity.*zed-stable"):
                    generate_packaging_files(manifest_path, cask_path, bucket_path)
                self.assertFalse(cask_path.exists())
                self.assertFalse(bucket_path.exists())

    def test_packaging_rejects_missing_or_unsafe_repository(self) -> None:
        for repository in (None, "", 123, "https://github.com/owner/repo", "owner/repo/extra",
                           "../repo", "owner/..", 'owner/repo"', "owner/repo\n",
                           "owner/#{system('bad')}", "owner/repo?redirect=evil"):
            for generator in (generate_homebrew_cask, generate_scoop_manifests):
                with self.subTest(repository=repository, generator=generator.__name__):
                    manifest = sample_manifest()
                    manifest["repository"] = repository
                    with self.assertRaisesRegex(ValueError, "repository"):
                        generator(manifest)

    def test_packaging_rejects_assets_from_a_different_repository(self) -> None:
        for factory in (sample_manifest, sample_universal_manifest):
            for generator in (generate_homebrew_cask, generate_scoop_manifests):
                with self.subTest(mode=factory.__name__, generator=generator.__name__):
                    manifest = factory()
                    manifest["repository"] = "cocoyamnut/zed-i18n"
                    with self.assertRaisesRegex(ValueError, "download_url does not match"):
                        generator(manifest)

    def test_generates_homebrew_cask_with_csv_version_and_language_assets(self) -> None:
        cask = generate_homebrew_cask(sample_manifest())

        self.assertIn('version "1.4.4,2"', cask)
        self.assertIn("v#{version.csv.first}-i18n.#{version.csv.second}", cask)
        self.assertIn('language "ko", default: true do', cask)
        self.assertIn('language "ja" do', cask)
        self.assertIn('sha256 arm: "mac-arm-ko-KR", intel: "mac-intel-ko-KR"', cask)
        self.assertIn('binary "#{appdir}/Zed.app/Contents/MacOS/cli", target: "zed"', cask)
        self.assertIn("auto_updates true", cask)
        self.assertTrue(cask.endswith("\n"))

    def test_packaging_uses_official_installed_identity_not_fork_tokens(self) -> None:
        for factory in (sample_manifest, sample_universal_manifest):
            manifest = factory()
            cask = generate_homebrew_cask(manifest)
            self.assertIn('cask "zed-i18n" do', cask)
            self.assertIn('app "Zed.app"', cask)
            self.assertIn('name "Zed"', cask)
            self.assertIn('conflicts_with cask: "zed"', cask)
            self.assertNotIn('Zed i18n.app', cask)
            for text in generate_scoop_manifests(sample_universal_manifest()).values():
                app = json.loads(text)
                self.assertEqual(app["bin"], [["bin\\zed.exe", "zed"]])
                self.assertEqual(app["shortcuts"], [["Zed.exe", "Zed"]])
                self.assertIn("Uninstall", " ".join(app["notes"]))

    def test_homebrew_uses_region_aware_language_args(self) -> None:
        cask = generate_homebrew_cask(sample_manifest(("pt-BR", "zh-CN", "zh-TW")))

        self.assertIn('language "pt-BR" do', cask)
        self.assertIn('language "zh-CN" do', cask)
        self.assertIn('language "zh-TW" do', cask)

    def test_homebrew_casks_support_macos_and_linux(self) -> None:
        for mode, manifest in (
            ("per-language", sample_manifest()),
            ("universal", sample_universal_manifest()),
        ):
            with self.subTest(mode=mode):
                cask = generate_homebrew_cask(manifest)
                self.assertNotIn("depends_on :macos", cask)
                self.assertNotIn("depends_on :linux", cask)
                self.assertIn("  on_macos do\n", cask)
                self.assertIn("  on_linux do\n", cask)
                self.assertIn("arm64_linux:", cask)
                self.assertIn("x86_64_linux:", cask)
                self.assertIn('command_wrapper "zed", content:', cask)
                self.assertIn('exec "#{staged_path}/zed.app/bin/zed" "$@"', cask)
                self.assertIn("brew upgrade --cask zed-i18n", cask)
                self.assertIn("brew uninstall --cask zed-i18n", cask)

    def test_homebrew_linux_assets_match_each_release_mode(self) -> None:
        localized = generate_homebrew_cask(sample_manifest())
        self.assertIn('arm64_linux: "linux-arm-ko-KR"', localized)
        self.assertIn('x86_64_linux: "linux-intel-ja-JP"', localized)
        self.assertIn("zed-i18n-#{language}-linux-#{arch}.tar.gz", localized)
        universal = generate_homebrew_cask(sample_universal_manifest())
        self.assertIn('arm64_linux: "lin-arm"', universal)
        self.assertIn('x86_64_linux: "lin-x64"', universal)
        self.assertIn("zed-i18n-linux-#{arch}.tar.gz", universal)

    def test_missing_linux_assets_fail_before_packaging_files_are_written(self) -> None:
        for mode, factory in (
            ("per-language", sample_manifest),
            ("universal", sample_universal_manifest),
        ):
            for arch in ("aarch64", "x86_64"):
                with self.subTest(mode=mode, arch=arch):
                    manifest = factory()
                    manifest["assets"] = [
                        asset
                        for asset in manifest["assets"]
                        if not (
                            asset["platform"] == "linux"
                            and asset["arch"] == arch
                            and (mode == "per-language" or asset["locale"] is None)
                        )
                    ]
                    manifest_path = self.tmp / f"{mode}-{arch}.json"
                    manifest_path.parent.mkdir(parents=True, exist_ok=True)
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                    cask_path = self.tmp / mode / arch / "Casks" / "zed-i18n.rb"
                    bucket_path = self.tmp / mode / arch / "bucket"
                    with self.assertRaisesRegex(ValueError, "linux"):
                        generate_packaging_files(manifest_path, cask_path, bucket_path)
                    self.assertFalse(cask_path.exists())
                    self.assertFalse(bucket_path.exists())

    def test_linux_assets_require_checksums_and_download_urls(self) -> None:
        for field in ("sha256", "download_url"):
            with self.subTest(field=field):
                manifest = sample_universal_manifest()
                asset = next(
                    asset for asset in manifest["assets"]
                    if asset["platform"] == "linux" and asset["locale"] is None
                )
                asset.pop(field)
                with self.assertRaisesRegex(ValueError, f"missing {field}"):
                    generate_homebrew_cask(manifest)

    def test_scoop_requires_universal_release_for_single_official_install_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires a universal release"):
            generate_scoop_manifests(sample_manifest())

    def test_per_language_release_fails_before_writing_any_packaging(self) -> None:
        manifest_path = self.tmp / "manifest.json"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(json.dumps(sample_manifest()), encoding="utf-8")
        cask_path = self.tmp / "out" / "zed-i18n.rb"
        bucket_path = self.tmp / "bucket"
        with self.assertRaisesRegex(ValueError, "requires a universal release"):
            generate_packaging_files(manifest_path, cask_path, bucket_path)
        self.assertFalse(cask_path.exists())
        self.assertFalse(bucket_path.exists())

    def test_scoop_keeps_package_manager_update_and_settings_behavior(self) -> None:
        app = json.loads(generate_scoop_manifests(sample_universal_manifest())["zed.json"])
        self.assertEqual(app["bin"], [["bin\\zed.exe", "zed"]])
        self.assertNotIn("pre_uninstall", app)
        self.assertIn("post_install", app)
        self.assertIn("[System.IO.File]::WriteAllText", "\n".join(app["post_install"]))

    def test_generate_packaging_files_writes_cask_and_bucket_files(self) -> None:
        manifest_path = self.tmp / "manifest.json"
        cask_path = self.tmp / "homebrew" / "Casks" / "zed-i18n.rb"
        bucket_path = self.tmp / "scoop" / "bucket"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(json.dumps(sample_universal_manifest()), encoding="utf-8")

        generate_packaging_files(manifest_path, cask_path, bucket_path)

        self.assertIn('cask "zed-i18n"', cask_path.read_text(encoding="utf-8"))
        self.assertEqual([p.name for p in bucket_path.glob("*.json")], ["zed.json"])

    def test_generate_packaging_files_rejects_partial_release_when_expected_locales_are_set(
        self,
    ) -> None:
        manifest_path = self.tmp / "manifest.json"
        cask_path = self.tmp / "homebrew" / "Casks" / "zed-i18n.rb"
        bucket_path = self.tmp / "scoop" / "bucket"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(json.dumps(sample_manifest(("ko-KR",))), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "missing locales: ja-JP"):
            generate_packaging_files(
                manifest_path,
                cask_path,
                bucket_path,
                expected_locales={"ja-JP", "ko-KR"},
            )

        self.assertFalse(cask_path.exists())
        self.assertFalse(bucket_path.exists())

    def test_generates_universal_homebrew_cask_without_language_stanzas(self) -> None:
        cask = generate_homebrew_cask(sample_universal_manifest())

        self.assertIn('cask "zed-i18n" do', cask)
        self.assertIn('version "1.4.4,2"', cask)
        self.assertIn('sha256 arm: "mac-arm", intel: "mac-intel"', cask)
        self.assertIn("Zed-i18n-macos-#{arch}.dmg", cask)
        self.assertNotIn("language ", cask)
        self.assertNotIn("#{language}", cask)
        self.assertIn("auto_updates true", cask)
        self.assertTrue(cask.endswith("\n"))

    def test_generates_scoop_manifest_with_official_package_token(self) -> None:
        manifests = generate_scoop_manifests(sample_universal_manifest())

        self.assertEqual(
            sorted(manifests),
            ["zed.json"],
        )

        universal = json.loads(manifests["zed.json"])
        self.assertEqual(universal["version"], "1.4.4-i18n.2")
        self.assertEqual(
            universal["architecture"]["64bit"]["url"],
            "https://github.com/LI-NA/zed-i18n/releases/download/v1.4.4-i18n.2/Zed-i18n-windows-x86_64.zip",
        )
        self.assertEqual(universal["architecture"]["64bit"]["hash"], "zip-x64")
        self.assertEqual(universal["shortcuts"], [["Zed.exe", "Zed"]])
        self.assertEqual(
            universal["env_set"]["ZED_UPDATE_EXPLANATION"],
            "Run 'scoop update zed' to update.",
        )
        self.assertEqual(
            universal["autoupdate"]["architecture"]["arm64"]["url"],
            "https://github.com/LI-NA/zed-i18n/releases/download/v$version/Zed-i18n-windows-aarch64.zip",
        )
        self.assertIn("notes", universal)

    def test_generate_packaging_files_accepts_universal_manifest_with_expected_locales(
        self,
    ) -> None:
        manifest_path = self.tmp / "manifest.json"
        cask_path = self.tmp / "homebrew" / "Casks" / "zed-i18n.rb"
        bucket_path = self.tmp / "scoop" / "bucket"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(json.dumps(sample_universal_manifest()), encoding="utf-8")

        generate_packaging_files(
            manifest_path,
            cask_path,
            bucket_path,
            expected_locales={"ja-JP", "ko-KR"},
        )

        self.assertIn('cask "zed-i18n"', cask_path.read_text(encoding="utf-8"))
        self.assertTrue((bucket_path / "zed.json").exists())
        self.assertEqual([p.name for p in bucket_path.glob("*.json")], ["zed.json"])

    def test_universal_manifest_without_alias_locales_fails_validation(self) -> None:
        manifest_path = self.tmp / "manifest.json"
        cask_path = self.tmp / "homebrew" / "Casks" / "zed-i18n.rb"
        bucket_path = self.tmp / "scoop" / "bucket"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(
            json.dumps(sample_universal_manifest(alias_locales=())), encoding="utf-8"
        )

        with self.assertRaisesRegex(ValueError, "no locale alias app assets"):
            generate_packaging_files(manifest_path, cask_path, bucket_path)

    def test_missing_required_architecture_fails(self) -> None:
        manifest = sample_manifest(("ko-KR",))
        manifest["assets"] = [
            asset
            for asset in manifest["assets"]
            if not (asset["platform"] == "macos" and asset["arch"] == "x86_64")
        ]

        with self.assertRaisesRegex(ValueError, "missing macos asset"):
            generate_homebrew_cask(manifest)


class PackagingWorkflowTests(unittest.TestCase):
    def test_update_packaging_workflow_runs_when_release_is_published(self) -> None:
        workflow = (Path.cwd() / ".github" / "workflows" / "i18n-update-packaging.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("release:", workflow)
        self.assertIn("types: [published]", workflow)
        self.assertIn(
            "uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2",
            workflow,
        )
        first_checkout = workflow.split("- name: Checkout zed-i18n", 1)[1].split(
            "- name: Setup uv",
            1,
        )[0]
        self.assertIn("persist-credentials: false", first_checkout)
        self.assertIn(
            "uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0",
            workflow,
        )
        self.assertIn("PACKAGING_REPOS_TOKEN", workflow)
        self.assertIn("gh release download", workflow)
        self.assertIn("Published release is not the repository latest release", workflow)
        self.assertIn("manifest.json", workflow)
        self.assertIn("SHA256SUMS.txt", workflow)
        self.assertIn("uv run zed-i18n generate-packaging", workflow)
        self.assertIn("--require-all-translations", workflow)
        self.assertIn("cocoyamnut/homebrew-zed-i18n", workflow)
        self.assertIn("cocoyamnut/scoop-zed-i18n", workflow)
        self.assertIn("diff --cached --quiet", workflow)

    def test_homebrew_validates_generated_working_tree_before_publishing(self) -> None:
        workflow = (Path.cwd() / ".github" / "workflows" / "i18n-update-packaging.yml").read_text(
            encoding="utf-8"
        )
        validation = workflow.index('brew readall --os=all --arch=all "$tap_name"')
        self.assertLess(workflow.index("uv run zed-i18n generate-packaging"), validation)
        self.assertLess(workflow.index('brew trust "$tap_name"'), validation)
        self.assertLess(validation, workflow.index("- name: Commit and push packaging repositories"))
        contract = workflow.index("brew ruby -- tests/check_homebrew_cask.rb")
        self.assertLess(validation, contract)
        self.assertLess(contract, workflow.index("- name: Commit and push packaging repositories"))
        self.assertIn(
            'ln -s "$GITHUB_WORKSPACE/packaging/homebrew" "$tap_parent/$tap_repo"',
            workflow,
        )
