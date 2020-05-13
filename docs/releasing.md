# Releasing Instructions

* look through git log and add new/interesting things to docs/changelog.md
* `VERSION=1.3.0`
* configure with `host_tests=misc/all_tests.conf`
* `cmd/build force $VERSION`
* `cmd/build push`
* ```git status --porcelain
 M misc/docker_images.txt
 M misc/docker_images.ver
```
* `git commit -a -m "$VERSION release"`
* `git tag -f -a latest_release -m "Latest release"`
* `git tag -a $VERSION -m "$VERSION release"`
* make sure your gcp setup is configured for bos-daq-testing
* `firebase/deploy.sh`
