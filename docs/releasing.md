# Releasing Instructions

* Update/check/commit headers and entries in in `docs/changelog.md`.
* Tag new version: `git tag -a -m "release-<RELEASE_VERSION>" release-<RELEASE_VERSION>`
* Push master to personal: `git push`
* Push tags to personal: `git push --tags`.
* Validate that all tests pass.
* Push master & tags to faucetsdn repo.
