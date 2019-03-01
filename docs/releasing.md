# Releasing Instructions

* Bring `release` branch to same version as `master`.
* Update new release version in `misc/RELEASE_VERSION`
* Update/check headers and entries in in `docs/changelog.md`.
* Commit changes using `git commit -a -m "release-$(cat misc/RELEASE_VERSION)"`
* Tag new version: `git tag -a -m "release-$(cat misc/RELEASE_VERSION)" release-$(cat misc/RELEASE_VERSION)`
* Check latest commit log message:
<pre>
~/daq$ git log -n 1
commit b7b6e3a44a3ad7b77abacacfadfc95004b21670d (HEAD -> release, tag: release-0.9.1)
Author: Trevor Pering <peringknife@google.com>
Date:   Tue Jan 29 11:45:12 2019 -0800

    Release 0.9.1
</pre>
* Push `release` branch, and verify Travis CI build completes successfully.
* Switch to `master` branch and merge in `release` branch, push to upstream repo.
* Push release tags: `git push --tags`.
* Push `master` and tags to any other origins (namely `faucetsdn/daq`).
