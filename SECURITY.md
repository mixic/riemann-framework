# Security Policy

## Scope

This repository is a research workbench: numerical experiments and Lean
formalization around the Riemann Hypothesis, together with speculative models
that are explicitly *not* claimed to be secure. There is no deployed service and
no released package. Most of what a security policy normally covers therefore
does not apply here, and the rest of this document says what does.

## Supported versions

There is nothing to support, in the usual sense:

- `git tag` is empty, and there are no GitHub releases.
- The Python package carries the single version `0.1.0` in
  [`python/pyproject.toml`](python/pyproject.toml). It has never been bumped, and
  the package has never been published to PyPI.
- The Lean side is pinned to a Mathlib commit hash in
  [`lake-manifest.json`](lake-manifest.json) rather than to a version.

Only the `main` branch exists, and only its current state is maintained. A
supported-versions matrix would be fiction, so there isn't one.

## What counts as a vulnerability

Anything that executes, or that lets someone else's code execute through this
project:

- arbitrary code execution or secret exposure in `scripts/`, in the Python
  package under `python/`, or in the Lean build that CI invokes;
- a compromised, typosquatted, or substituted dependency — including the pinned
  Mathlib revision in `lake-manifest.json` and the GitHub Actions used by
  [`.github/workflows/ci.yml`](.github/workflows/ci.yml);
- anything that lets a third party influence a build or an artifact committed
  under `output/`.

## What is not a vulnerability

- **Cryptographic claims about DSIN.** The Dimension-Shift Involution Network is
  a speculative proposal, and this repository states plainly that it has no
  security proof. More than that:
  [`docs/dimension_shift_quantum_communication.md`](docs/dimension_shift_quantum_communication.md)
  §4.1 proves that its central observable *cannot* support one, and exhibits an
  attack that recovers every transmitted bit while producing the readings of a
  noiseless channel. A report that DSIN is insecure is a **research finding, not
  a vulnerability**. Please open a regular issue; negative results are a
  documented and deliberate part of this project, not a threat to it.
- **Mathematical claims.** The statements about the Riemann Hypothesis are claims
  to be falsified by argument, not exploited. Use the issue tracker.
- **Numerical bugs, wrong figures, or incorrect documentation.** Also issues.

## Reporting a vulnerability

For anything in the first list, use GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability):
**Security → Report a vulnerability** on this repository.

That channel has to be enabled by the maintainer. If the button is missing, open
an issue titled "Private security contact request" containing no details, and a
private channel will be arranged. No email address is published in this
repository; please do not scrape one from commit metadata.

Include what you did, what happened, and what you expected, with a minimal
reproduction if you have one.

## What to expect

This is a single-maintainer research project with no releases and no downstream
users depending on it. There is no response-time guarantee and no bounty.
Reports are read and answered on a best-effort basis. Where a fix is warranted it
lands on `main` together with a test that pins it, matching the style of the rest
of the repository — the test suite is where this project records what it knows.
