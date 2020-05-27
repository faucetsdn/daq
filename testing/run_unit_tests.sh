#!/bin/bash -e

MINCOVERAGE=92
SCRIPTPATH=$(readlink -f "$0")
TESTDIR=`dirname $SCRIPTPATH`
BASEDIR=`readlink -f $TESTDIR/..`
cd $BASEDIR

venv/bin/coverage erase

PYTHONPATH=$BASEDIR/daq:$BASEDIR/mininet:$BASEDIR/faucet:$BASEDIR/forch venv/bin/coverage run \
    --source $BASEDIR/daq \
    -m unittest discover \
    -s $TESTDIR/unit/ \
    -p "test_*.py"

venv/bin/coverage combine || true
venv/bin/coverage report -m
