#!/bin/bash

MINCOVERAGE=92
SCRIPTPATH=$(readlink -f "$0")
TESTDIR=`dirname $SCRIPTPATH`
BASEDIR=`readlink -f $TESTDIR/..`
cd $BASEDIR || exit 1

#echo $SCRIPTPATH $TESTDIR $BASEDIR
#TESTCMD="PYTHONPATH=$BASEDIR $BASEDIR/venv/bin/coverage run --parallel-mode --source $BASEDIR/daq"
#SRCFILES="find $TESTDIR/unit/*/test_*py $TESTDIR/integration/experimental_api_test_app.py -type f"
#SRCFILES="find $TESTDIR/unit/test_*.py -type f"

#coverage erase || exit 1
#$SRCFILES | xargs realpath | shuf | parallel --delay 1 --bar --halt now,fail=1 -j 2 $TESTCMD || exit 1
#echo "$SRCFILES | xargs realpath | shuf | $TESTCMD"
#$SRCFILES | xargs realpath | shuf | $TESTCMD || exit 1
#coverage combine
#coverage report -m --fail-under=$MINCOVERAGE || exit 1
$BASEDIR/venv/bin/coverage erase || exit 1
PYTHONPATH=$BASEDIR/daq $BASEDIR/venv/bin/coverage run --source $BASEDIR/daq -m unittest discover -s $TESTDIR/unit/ -p "test_*.py" || exit 1
$BASEDIR/venv/bin/coverage combine
$BASEDIR/venv/bin/coverage report -m || exit 1
