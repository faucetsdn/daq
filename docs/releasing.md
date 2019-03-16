# Releasing Instructions

* Bring local `release` branch to same commit as `master`
* Update new release version in `misc/RELEASE_VERSION`
* Update/check headers and entries in in `docs/changelog.md`
* Commit changes:<br/>`git commit -a -m "release-$(cat misc/RELEASE_VERSION)"`
* Tag new version:<br/>`git tag -a -m "release-$(cat misc/RELEASE_VERSION)" release-$(cat misc/RELEASE_VERSION)`
* Check latest commit log message:
<pre>
~/daq$ <b>git log -n 1</b>
commit b7b6e3a44a3ad7b77abacacfadfc95004b21670d (HEAD -> release, tag: release-0.9.1)
Author: Smarmy Monkey <smarmy@monkey.com>
Date:   Tue Jan 29 11:45:12 2019 -0800

    release-0.9.1
</pre>
* Push `release` branch, <b>and verify Travis CI build completes successfully.</b>
* Switch to `master` branch and merge in `release` branch.
* Push `master` and tags:<br/>`git push --tags origin master`
* Push `master` and tags to any other origins:<br/>`git push --tags faucet master`
* Verify all is well with the world:
<pre>
~/daq$ <b>git log -n 2 origin/master</b>
commit b29ce8e541c64e686a0c9b28a31f97aa6c9af785 (<b>tag: release-0.9.5, origin/release, origin/master, origin/HEAD, faucet/master, release, master</b>)
Author: Smarmy Monkey <smarmy@monkey.com>
Date:   Sat Mar 16 09:27:42 2019 -0700

    release-0.9.5

commit b7afb27891ce8726795a399b2cd0d9466d459fcb
Author: Smarmy <grafnu@users.noreply.github.com>
Date:   Sat Mar 16 09:25:27 2019 -0700

    Adding qualification description template (#110)
</pre>
