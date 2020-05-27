#!/bin/bash -e

MINCOVERAGE=92
SCRIPTPATH=$(readlink -f "$0")
TESTDIR=`dirname $SCRIPTPATH`
BASEDIR=`readlink -f $TESTDIR/..`
cd $BASEDIR

coverage erase

PYTHONPATH=$BASEDIR/daq:$BASEDIR/mininet:$BASEDIR/faucet:$BASEDIR/forch coverage run \
    --source $BASEDIR/daq \
    -m unittest discover \
    -s $TESTDIR/unit/ \
    -p "test_*.py"

coverage combine || true
coverage report -m
