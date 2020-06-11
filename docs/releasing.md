# Releasing Instructions

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
* make sure your gcp setup is configured for bos-daq-testing
* `firebase/deploy.sh`
* `git checkout release_testing && git reset --hard $VERSION`
* `git push`
* QA pass to make sure everything is ok.
* make sure your gcp setup is configured for daq-qualification-labs
* `firebase/deploy.sh`
* `git checkout release_stable && git reset --hard $VERSION`
