#!/bin/bash
set -e -x

# Some google packages will require this as a prerequisite.
addgroup --gid 5000 eng

# Replace install-time package configuration with Rapture.
#echo "deb https://rapture-prod.corp.google.com goobuntu-rodete-base-stable main" > /etc/apt/sources.list
echo "" > /etc/apt/sources.list
rm -f /etc/apt/sources.list.d/*
curl https://rapture-prod.corp.google.com/doc/rapture-public-keyring.gpg | apt-key add -

# The postinst for the pbuilder package will fail without this
# preseed. It never actually gets used; this is just to prevent
# it from entering an infinite loop.
sudo debconf-set-selections << EOF
pbuilder pbuilder/mirrorsite string http://archive.ubuntu.com/ubuntu
EOF

add_rapture_repo() {
  echo "deb https://rapture-prod.corp.google.com $1 $2" >> /etc/apt/sources.list
}
add_rapture_repo glinux-base-rodete-stable main
add_rapture_repo glinux-extra-rodete-stable main
add_rapture_repo glinux-priority-rodete-stable main
add_rapture_repo glinux-canaries-rodete-stable main
add_rapture_repo glinux-priority-extra-rodete-stable main
add_rapture_repo goobuntu-utils-stable main
add_rapture_repo enterprise-sdn-faucet-core-unstable main

apt-get -q update
apt-get -q -y install glinux-build git devscripts
