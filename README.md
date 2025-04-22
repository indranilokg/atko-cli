> :warning: Work in Progress: Only a few Okta resources are supported at this time. :warning:

# Atko CLI (reverse Okta CLI)

`aktocli` is [Bizarro World](https://en.wikipedia.org/wiki/Bizarro) version of [Okta CLI](https://github.com/oktadeveloper/okta-cli). It is a completely different approach to manage Okta resources using different technology stack(***Python***). The primarily goal of Akto CLI is automate actions like create, update and delete resources that would require many clicks in the Okta UI. :tada:

Supported resources:

* User
* Groups
* Applications

## Availability

We are in pre-alpha stage, meaning there is still a lot features left to implemented.

## Usage

```bash
$ akto --help
Usage: akto [OPTIONS] COMMAND [ARGS]...

  CLI tool for your Okta org.

Options:
  -h, --help  Show this message and exit.

Commands:
  config  Store configuration values.
  users   Okta User Management
...
```

## Documentation

Read the [official docs](https://atko-cli.github.com/manual/) for more information. (Not Implemented)


<!-- this anchor is linked to from elsewhere, so avoid renaming it -->
## Installation

### macOS

`atkocli` is available via Homebrew. (Not Implemented)

#### Homebrew

Install:

```bash
brew install github/indranilokg/atko-cli
```

Upgrade:

```bash
brew upgrade atko-cli
```

### Other platforms

Download packaged binaries from the [releases page][].

### Build from source

See here on how to [build Atko CLI from source](/docs/source.md). (Not Implemented)

### Local Development and Testing

To test the CLI locally during development:

1. Create and activate a virtual environment named "localtest":
```bash
# Create virtual environment
python -m venv localtest

# Activate the environment
# On macOS/Linux:
source localtest/bin/activate
# On Windows:
localtest\Scripts\activate
```

2. Install the package in editable mode:
```bash
pip install -e .
```

This installation method allows you to modify the source code and test changes immediately without reinstalling the package. Any changes you make to the code will be reflected when you run the `atko` command.

3. Test the CLI:
```bash
# Verify the installation
atko --help

# Try specific commands
atko config --help
atko users --help
```

4. When you're done testing, deactivate the virtual environment:
```bash
deactivate
```
```

## Author

* Indranil - [indranilokg](https://github.com/indranilokg), Creator :tada:
* Noi Narisak - [noinarisak](https://github.com/indranilokg), Contributor

<!-- # Markdown Mapping -->
[docs]: https://atko-cli.github.com/manual
[releases page]: https://github.com/indranilokg/atko-cli/releases/latest
[contributing page]: https://github.com/indranilokg/atko-cli/trunk/.github/CONTRIBUTING.md
