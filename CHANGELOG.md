# Changelog

This is the changelog for RedPepper.

## [Unreleased]

### Added

- Disable connection keep-alive pings if `ping_interval` is set to `0`.
- Add `changed_operations` parameter to state runner to allow forcing certain operations to run.

## [0.3.1]

### Changed

- Update operations that run system commands to use `trio.to_thread.run_sync` for better concurrency.

## [0.3.0]

### Changed

- **Breaking change:** Restructure state file format for better execution flow control.
  - This is not backwards compatible. All state files must be updated as well as all
    Manager and Agent instances before states can be executed.

## [0.2.0]

### Changed

- **Breaking change:** Migrate operations and requests to be asynchronous.
  - Non-asynchronous operations are still functional, but expect support for them to
    be removed in a future release.
- **Breaking change:** Make the communication protocol more RPC-like.
  - This is backwards compatible for the initial agent authentication, but running commands
    will not work until the Manager and Agent are both updated.

## [0.1.4]

### Changed

- Improve WebSocket status display in Events and Commands view.
- Improve navigation in the console.

### Fixed

- Update references to `uv` install location since `uv` 0.5.0 release.

## [0.1.3]

### Changed

- Improve styling in the console.

### Fixed

- Fix root ca certificate path in step-keypair tools.
- Fix URL path to favicon SVG in console.

## [0.1.2]

### Fixed

- Add `redpepper` dependency for manager, agent, and common packages.

## [0.1.1]

### Changed

- Use strings for request IDs instead of integers.

## [0.1.0]

### Changed

- **BREAKING CHANGE**: Use MessagePack instead of Protobuf for manager/agent communications.
  **This is not backwards compatible. All Manager and Agent instances must be updated at the same time.**
- Prompt for username if not supplied to `install-login` tool.
