#!/bin/bash -eu

tag=$1
if [[ -z $tag ]]; then
  echo "Tag is empty.\nUsage: ./set_version_tag.sh <tag>"
  exit
fi
debchange --newversion $tag -b "New upstream release $tag"

# Change ID hook
hook=`git rev-parse --git-dir`/hooks/commit-msg
mkdir -p $(dirname $hook)
curl -Lo $hook https://gerrit-review.googlesource.com/tools/hooks/commit-msg
chmod +x $hook

git add debian/changelog
