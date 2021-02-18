#!/bin/bash -e

MINCOVERAGE=92
SCRIPTPATH=$(readlink -f "$0")
TESTDIR=`dirname $SCRIPTPATH`
BASEDIR=`readlink -f $TESTDIR/..`
cd $BASEDIR

source venv/bin/activate
source bin/config_base.sh
coverage erase

export PYTHONPATH=$BASEDIR/daq:$BASEDIR/mininet:$BASEDIR/faucet:$BASEDIR/forch:$BASEDIR/bin/python:$BASEDIR/libs:$BASEDIR/libs/proto
coverage run \
    --source $BASEDIR/daq,$BASEDIR/bin/python/ \
    -m unittest discover \
    -s $TESTDIR/unit/ \
    -p "test_*.py"

coverage combine || true
coverage report -m
if [ -f .coverage ]; then
    echo Generating codecov report \#unit...
    codecov -F unit 
fi
