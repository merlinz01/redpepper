# Changelog

This is the changelog for RedPepper.

## [Unreleased]

### Changed

- **BREAKING CHANGE**: Use MessagePack instead of Protobuf for manager/agent communications.
  **This is not backwards compatible. All Manager and Agent instances must be updated at the same time.**
- Prompt for username if not supplied to `install-login` tool.
