#!/bin/bash -e

ROOT=$(dirname $0)/..
cd $ROOT

bin/build.sh

schema_root=../schemas

errorfile=`mktemp`
rm -f $errorfile

build=y
force=n
ignoreset=.

while getopts ":fn" opt; do
    case $opt in
        f) force=y
            ;;
        n) build=n
           ;;
        \?) echo "Usage: test.sh [-f] [-n]"
            exit -1
            ;;
    esac
done

jarfile=$(realpath build/libs/validator-1.0-SNAPSHOT-all.jar)

outroot=out
rm -rf $outroot

if [ "$build" == y ]; then
    bin/build.sh
fi

schemas=$(cd $schema_root && ls)
if [ -z "$schemas" ]; then
    echo No schemas found.
    false
fi
for schema in $schemas; do
    rootdir=$schema_root/$schema
    subsets=$(cd $rootdir; ls -d *.tests)
    for subset in $subsets; do
        if [ -z "$subset" ]; then
            echo Schema $schema has no .tests dirs.
            false
        fi
        schemaname=${subset%.tests}.json
        testfiles=$(cd $rootdir/$subset; ls *.json)
        for testfile in $testfiles; do
            outfile=${testfile%.json}.out
            testdir=$rootdir/$subset
            testpath=$testdir/$testfile
            expected=$testdir/$outfile
            outdir=$outroot/${testdir#${schema_root}/}
            mkdir -p $outdir
            output=$outdir/$outfile
            
            error=0
            reltest=${testpath#$rootdir/}
            (cd $rootdir; java -jar $jarfile $schemaname $reltest $ignoreset) 2> $output || error=$?
            if [ $force == y ]; then
                diff $expected $output || echo Updating $expected && cp $output $expected
            else
                diff -b $expected $output || (echo Expectation letdown, to force: cp $output $expected | tee -a $errorfile)
            fi
        done
    done
done

echo

if [ -f $errorfile ]; then
    echo Validation errors found:
    cat $errorfile
    false
fi

echo Done with validation.
              
