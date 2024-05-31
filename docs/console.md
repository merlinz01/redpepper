# RedPepper Console

RedPepper includes a web console as the primary means of interacting with the Manager and sending commands to Agents.

## Installation

The console is installed and configured by default when RedPepper is installed.
See [Installation](installation.md) for more info.

## Usage

Simply navigate to the host and port configured as the API server,
e.g. `https://my.redpepper.manager.instance:5001/`.
The console is served as a single-page application at the base path of the API server.

Log in with the credentials configured in `manager.yml`.
You will have to manually set up your two-factor authentication app with the secret you configured.

You can send commands and view their results from the console.

You can edit the configuration and data files for the agents with syntax highlighting and more from the comforts of your web browser, thanks to the [Ace Editor](https://ace.c9.io) embedded in the console.
