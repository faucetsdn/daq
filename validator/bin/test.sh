#!/bin/bash -e

ROOT=$(dirname $0)/..
cd $ROOT

outdir=out/

bin/build.sh

schemas=$(cd schemas; ls *.json)
if [ -z "$schemas" ]; then
    echo No schemas found.
    false
fi
for schema in $schemas; do
    name=${schema%.json}
    tests=$(cd schemas/$name/; ls *.json)
    rm -rf $outdir
    mkdir -p $outdir
    if [ -z "$tests" ]; then
        echo Testing $schema has no tests.
    fi
    for test in $tests; do
        target=schemas/$name/$test
        expected=${target%.json}.out
        output=${outdir}${expected##*/}
        error=0
        java -jar build/libs/validator-1.0-SNAPSHOT-all.jar schemas/$schema $target 2> $output || error=$?
        echo Testing $schema against $target result $error
        diff $expected $output || (echo Expected result \< $expected does not match output \> $output; false)
    done
done

echo Done with validation.
              
