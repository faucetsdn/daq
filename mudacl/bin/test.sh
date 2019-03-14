#!/bin/bash -e

ROOT=$(dirname $0)/..
cd $ROOT
SETUP=setup
MUD_FILES=../mud_files/
OUTDIR=out

./gradlew shadow

echo Running mudacl regression test...
rm -rf $OUTDIR || sudo rm -rf $OUTDIR
mkdir -p $OUTDIR/acl_templates $OUTDIR/port_acls

java -jar build/libs/mudacl-1.0-SNAPSHOT-all.jar ../mud_files $OUTDIR/acl_templates/ \
     $SETUP/faucet.yaml $SETUP/devices.json $SETUP/cabling.json $OUTDIR/port_acls/

echo Compare $OUTDIR/acl_templates/ with $SETUP/acl_templates/...
diff -r $OUTDIR/acl_templates/ $SETUP/acl_templates/

echo Compare $OUTDIR/port_acls/ with $SETUP/port_acls/...
diff -r $OUTDIR/port_acls/ $SETUP/port_acls/
