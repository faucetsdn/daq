#!/bin/bash

set -eux
ls -alrt git/
uname -a
echo "${TMPDIR}"
cd git/benz-build-source
sudo kokoro/setup.sh
mkdir -p "${TMPDIR}/binary/"
mkdir -p "${TMPDIR}/glinux-build"

ls -alrt
GIT_URL=rpc://perry-internal/daq bin/setup_remote faucet
VERSION=$(git describe)
debchange --newversion $VERSION -b "New upstream release"

glinux-build -type="binary" -base-path="${TMPDIR}/glinux-build" -additional-repos="enterprise-sdn-faucet-core-unstable" -name="rodete" . "${TMPDIR}/binary/"
mkdir -p binary
cp ${TMPDIR}/binary/* binary/
