#!/bin/bash -e

MINCOVERAGE=92
SCRIPTPATH=$(readlink -f "$0")
TESTDIR=`dirname $SCRIPTPATH`
BASEDIR=`readlink -f $TESTDIR/..`
cd $BASEDIR

$BASEDIR/venv/bin/coverage erase

PYTHONPATH=$BASEDIR/daq $BASEDIR/venv/bin/coverage run \
    --source $BASEDIR/daq \
    -m unittest discover \
    -s $TESTDIR/unit/ \
    -p "test_*.py"

$BASEDIR/venv/bin/coverage combine || true
$BASEDIR/venv/bin/coverage report -m
