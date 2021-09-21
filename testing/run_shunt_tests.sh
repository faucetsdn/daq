#!/bin/bash -e

MINCOVERAGE=92
SCRIPTPATH=$(readlink -f "$0")
TESTDIR=`dirname $SCRIPTPATH`
BASEDIR=`readlink -f $TESTDIR/..`
cd $BASEDIR

source venv/bin/activate

export PYTHONPATH=$BASEDIR/shunt:$BASEDIR/bin/python
python3 \
    -m unittest discover \
    -s $TESTDIR/shunt_tests/ \
    -p "test_*.py"
