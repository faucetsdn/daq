# Releasing Instructions

* look through git log and add new/interesting things to docs/changelog.md
* e.g. `VERSION=1.3.0`
* configure with `host_tests=misc/all_tests.conf`
* `cmd/build force $VERSION`
* `cmd/build push`
* Check generated files:
```
git status --porcelain
 M misc/docker_images.txt
 M misc/docker_images.ver
```
* `git commit -a -m "$VERSION release"`
* `git push`
* `git tag -a $VERSION -m "$VERSION release"`
* `git push --tags`
* make sure your gcp setup is configured for bos-daq-testing
* `firebase/deploy.sh`
* QA pass to make sure everything is ok.
* `git checkout release_stable && git reset --hard $VERSION`
* `git push`
