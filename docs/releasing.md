# Releasing Instructions

* Bring `release` branch to same version as `master`.
* Determine new release version (e.g. `0.9.1`) updated from `misc/RELEASE_VERSION`.
* Update and commit new version in `misc/RELEASE_VERSION`.
* Update and commit entries in in `docs/changelog.md`.
* Tag new version: `git tag -a -m "$(cat misc/RELEASE_VERSION)" release-$(cat misc/RELEASE_VERSION)`
* Check latest commit log message:
<pre>
~/daq$ git log -n 1
commit b7b6e3a44a3ad7b77abacacfadfc95004b21670d (HEAD -> release, tag: release-0.9.1)
Author: Trevor Pering <peringknife@google.com>
Date:   Tue Jan 29 11:45:12 2019 -0800

    Release 0.9.1
</pre>
* Push release tags: `git push --tags`.
* Push `release` branch.
* Verify Travis CI build for `release` branch completes successfully.
* Switch to `master` branch and merge in `release` branch.
* Push `master` branch.
* Make sure `master` branch _and tags_ are pushed to `faucetsdn` origin.
