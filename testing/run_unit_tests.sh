#!/bin/bash

MINCOVERAGE=92
SCRIPTPATH=$(readlink -f "$0")
TESTDIR=`dirname $SCRIPTPATH`
BASEDIR=`readlink -f $TESTDIR/..`
cd $BASEDIR || exit 1

$BASEDIR/venv/bin/coverage erase || exit 1
PYTHONPATH=$BASEDIR/daq $BASEDIR/venv/bin/coverage run --source $BASEDIR/daq -m unittest discover -s $TESTDIR/unit/ -p "test_*.py" || exit 1
$BASEDIR/venv/bin/coverage combine
$BASEDIR/venv/bin/coverage report -m || exit 1
