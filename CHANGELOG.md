# Changelog

This is the changelog for RedPepper.

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
