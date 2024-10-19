# Changelog

This is the changelog for RedPepper.

## [Unreleased]

### Security

- Use `argon2` for password hashing.

### Fixed

- Update various usages of console assets path.

## [0.0.13]

### Changed

- Update default command log path.
- Install `redpepper-step-ca` systemd service file by default when running `setup-step-ca` on Linux.
- Use existing provisioner password file for manager and api certificate installation.

## [0.0.12]

### Fixed

- Include both `.yml` and `.yaml` files in the default configuration dirs, but change tools to use `.yml` extension.
- Add newline to end of step renew cron job.
- Fix default path to step CA file.

## [0.0.11]

### Fixed

- Update default operations cache directory.
- Create operations cache directory in install script.
- Reset umask in install script so systemd doesn't complain about permissions.

### Changed

- Update default `step` config path in `redpepper-tools`.

## [0.0.10]

### Added

- Add `--stepbinary` flag with default to step-related tools.

### Changed

- Update default config paths and include option.
- Improve error messages for missing certificate/key files.

### Fixed

- Fix systemd service file commands for `redpepper-agent` and `redpepper-manager`.

## [0.0.9]

### Fixed

- Various improvements to the `install-step-ca` script.

## [0.0.8]

### Changed

- Update various default paths for installation tools.

## [0.0.7]

### Changed

- Update installation docs with new installation and setup commands.
- Add checksum file to GitHub release assets.
- Update console install script with default download path.
- Use [`ruff`](https://docs.astral.sh/ruff) for Python formatting and linting.
- Add default requests and operations as Python packages.

## [0.0.6]

### Added

- Install `redpepper-tools` along with the Manager and Agent when using the default install script.

## [0.0.5]

### Changed

- Update install scripts to use `uv` for deployment.
- Migrate various utilities from shell scripts to Python scripts in `redpepper-tools`.

## [0.0.4]

(No changes)

## [0.0.3]

### Changed

- Update `pyproject.toml` project URL's.
- Change manager `fastapi[standard]` dependency to `fastapi`.

## [0.0.2]

### Changed

- Update `pyproject.toml` metadata.

## [0.0.1]

### Changed

- Use [`uv`](https://docs.astral.sh/uv) for workspace and dependency management.
