> :warning: Work in Progress: Only a few Okta resources are supported at this time. :warning:

# Atko CLI (reverse Okta CLI)

`akto` is [Bizarro World](https://en.wikipedia.org/wiki/Bizarro) version of [Okta CLI](https://github.com/oktadeveloper/okta-cli). It is a completely different approach to manage Okta resources using different technology stack(***Python***). The primarily goal of Akto CLI is automate actions like create, update and delete resources that would require many clicks in the Okta UI. :tada:

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
```

## Documentation

Read the [official docs](https://okt-cli.github.com/manual/) for more information. (Not Implemented)


<!-- this anchor is linked to from elsewhere, so avoid renaming it -->
## Installation

### macOS

`atko` is available via Homebrew. (Not Implemented)

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

## Author

* Indranil - [indranilokg](https://github.com/indranilokg), Creator :tada:
* Noi Nariak - [noinarisak](https://github.com/indranilokg), Contributor

<!-- # Markdown Mapping -->
[docs]: https://atko-cli.github.com/manual
[releases page]: https://github.com/indranilokg/atko-cli/releases/latest
[contributing page]: https://github.com/indranilokg/atko-cli/trunk/.github/CONTRIBUTING.md
