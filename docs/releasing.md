# Releasing Instructions

These instructions assume that `faucetsdn/daq` is your git remote _origin_.

* look through git log (`git log release_stable..HEAD --pretty=oneline`) and add new/interesting things to docs/changelog.md
* e.g. `VERSION=1.3.0`
* configure with `host_tests=config/modules/all.conf`
* `cmd/build force $VERSION`
* `cmd/build push`
* Check generated files:
```
git status --porcelain
 M etc/docker_images.txt
 M etc/docker_images.ver
```
* `git commit -a -m "$VERSION release"`
* `git push`
* `git tag -a $VERSION -m "$VERSION release"`
* `git push --tags`
* `firebase/deploy.sh bos-daq-testing`
* `git checkout release_testing && git reset --hard $VERSION`
* `git push`
* QA pass to make sure everything is ok.
* `firebase/deploy.sh daq-qualification-labs`
* `git checkout release_stable && git reset --hard $VERSION`
* `git push`
