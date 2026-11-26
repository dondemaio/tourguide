# Testing

From the repository root, using Python 3.11 in a virtual environment:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest
```

The baseline suite uses synthetic matrices and mocked HTTP responses. No map data, credentials, running OSRM instance or external network requests are needed during tests. Dependency installation requires package access. GitHub Actions runs the same suite on pull requests to and pushes to develop.

These tests cover existing supported behavior, not all desired constraints. Mandatory disjunction enforcement, unreachable legs and input validation are addressed in PR #4; opening-hours exceptions, clipping and timezone semantics in PR #5. Add regression tests with those fixes rather than treating current defects as expected behavior.
