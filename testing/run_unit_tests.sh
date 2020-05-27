#!/bin/bash -e

MINCOVERAGE=92
SCRIPTPATH=$(readlink -f "$0")
TESTDIR=`dirname $SCRIPTPATH`
BASEDIR=`readlink -f $TESTDIR/..`
cd $BASEDIR

source venv/bin/activate

coverage erase

PYTHONPATH=$BASEDIR/daq:$BASEDIR/mininet:$BASEDIR/faucet:$BASEDIR/forch coverage run \
    --source $BASEDIR/daq \
    -m unittest discover \
    -s $TESTDIR/unit/ \
    -p "test_*.py" || exit 1

coverage combine || true
coverage report -m
