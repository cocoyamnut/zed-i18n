# Installed identity: official stable Zed

The next release replaces the **official stable Zed application**, rather than
installing a separately named “Zed i18n” application. This is an intentional
compatibility change, not a claim that this fork is published or signed by Zed
Industries. Localization, the `zed-i18n` build label, release asset names and
GitHub release update source remain fork-specific.

## Source of truth

Identity values are checked against `config/project.toml`'s pinned upstream
`zed-industries/zed` commit `d25fa01ccd788d812f236810b71af4feff6b2e38` (v1.25.2):

| Platform | Installed identity | Authoritative upstream source |
| --- | --- | --- |
| macOS | `Zed.app`, `dev.zed.Zed`, `zed` CLI | `crates/zed/Cargo.toml`, `script/install.sh` |
| Linux tarball | `zed.app`, `dev.zed.Zed.desktop`, `zed` CLI/icon | `script/bundle-linux`, `script/install.sh` |
| Windows installer | `Zed`, `{autopf}\Zed`, `Zed.exe`, official stable Inno/Appx/shell IDs | `script/bundle-windows.ps1`, `crates/zed/resources/windows/zed.iss`, `crates/explorer_command_injector/AppxManifest.xml` |

The upstream Windows installer mutex (`Zed-Stable-Instance-Mutex`) differs from
its runtime identifier-derived mutex (`Zed-Editor-Stable-Instance-Mutex`). Both
are preserved exactly; this change does not attempt to fix upstream behavior.

The contract test compares real upstream identity files before and after the
distribution overlay. Preview/nightly/dev identities are not changed.

## Installation and migration

- These builds cannot coexist independently with official **stable** Zed at the
  same location. Close Zed before replacing it; back up settings and user data.
  Existing official user data/settings and file associations can be shared.
- Existing separately named `Zed i18n.app` / Windows `Zed i18n` installations
  are not silently deleted or migrated. Remove the old application using the
  installer/package manager that owns it, without deleting wanted user data,
  then install the new release. Do not run an old uninstaller after a new
  installation without checking which shared registrations it removes.
- Homebrew keeps the fork-qualified cask token `zed-i18n`, but installs
  `/Applications/Zed.app` and a `zed` CLI. Remove the official `zed` cask first;
  the generated cask declares that conflict. The tap stays fork-specific.
- Scoop uses **`zed.json`**, so the installed app root is `apps/zed` and the
  shortcut/shim are `Zed` / `zed`. The bucket stays `zed-i18n`; use the
  bucket-qualified package `zed-i18n/zed`. Remove the existing official `zed`
  or old `zed-i18n*` package before switching. There is no automatic package
  ownership transfer. Only universal releases support this single identity;
  locale-specific Scoop packages are no longer generated.
- The pinned upstream has no Debian package recipe. Our Debian package is
  therefore an additional system-packaging format, not an upstream path
  equivalent: `/usr/lib/zed`, `/usr/bin/zed`, and `dev.zed.Zed.desktop`.
  The fork's `zed-i18n` dpkg package token retains upgrade continuity and
  conflicts with a package named `zed`. The official shell install instead
  uses `~/.local/zed.app` and `~/.local/bin/zed`; remove or adjust an existing
  user-scoped installation to avoid PATH/desktop precedence ambiguity.
- No updater, installer, certificate, credentials, or installed applications
  on a user's device are changed by this source patch. Matching names and
  IDs cannot confer the official vendor's code-signing identity or trust.

## Publication order

1. Review and commit this source change; do not reuse existing release assets.
2. Build a **new** fork release revision for all supported platforms. Verify
   app bundle names/IDs, Windows installer and portable payloads, Linux archive
   roots/desktop metadata, CLI invocation, localization and fork updater URL.
   Test replacement and uninstall behavior on native OS test machines,
   including signing/notarization and Explorer registration where applicable.
3. Publish that release's binaries/checksums/manifest together.
4. New-build metadata declares `installed_identity: "zed-stable"`; the package
   generator rejects absent or different markers, including old releases.
   This declaration is not a substitute for inspecting native payloads. Never
   add it to an old manifest to bypass validation.
5. Only then generate and publish Homebrew/Scoop manifests from that exact
   release. Existing v1.25.2-i18n.1 binaries have the old identity and must not
   be referenced by these new install targets. Remove obsolete Scoop manifests
   from the bucket as part of its existing update workflow.

Local Python/patch-contract tests do not substitute for these native build and
installation checks. No release, tag, remote package update, or push is part of
this local change.
