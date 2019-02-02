# Releasing Instructions

* Bring `release` branch to same version as master.
* Determine new release version (e.g. `0.9.1`) updated from `misc/RELEASE_VERSION`
* Update and commit new version in `misc/RELEASE_VERSION`
* Tag new version: `git tag -a -m "Release 0.9.1" release-0.9.1`
* Check latest commit log message:
<pre>
~/daq$ git log -n 1
commit b7b6e3a44a3ad7b77abacacfadfc95004b21670d (HEAD -> release, tag: release-0.9.1)
Author: Trevor Pering <peringknife@google.com>
Date:   Tue Jan 29 11:45:12 2019 -0800

    Release 0.9.1
</pre>
* Push `release` branch.
* Switch to `master` branch and merge in `release` branch.
* Push release tags: `git push --tags`.
* Push `master` branch .
* Verify Travis CI build for `release` branch completes successfully.
* Make sure `master` branch and tags are pushed to `faucet` origin.
