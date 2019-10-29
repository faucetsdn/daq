# reporting_utils
# Helper functions written in bash for simplifying report writing

_______REPORT_DIVIDER="--------------------"

# write_out_result
# All inputs EXCEPT $REPORT are variables (not files)
# Intended to write out output for one test
# to the .md report

function write_out_result {
    local REPORT=$1
    local TEST_NAME=$2
    local TEST_DESCRIPTION=$3
    local LOG=$4
    local RESULT_AND_SUMMARY=$5

    cat <<END >> $REPORT
$_______REPORT_DIVIDER
$TEST_NAME
$_______REPORT_DIVIDER
$TEST_DESCRIPTION
$_______REPORT_DIVIDER
$LOG
$_______REPORT_DIVIDER
$RESULT_AND_SUMMARY

END
}

# check_for_fails_in
# Input is an array of variables (not files!) containing text
# All inputs EXCEPT $REPORT are variables (not files)
# Intended for use by test running bash scripts to return a non-zero
# exit code if any test in a module fails
# This way, the firebase dashboard shows 'red' if there has been a failure
# in any test

function check_for_fails_in() {
    local arr=("$@")
    local __result="false"
    for log in "${arr[@]}";
        do
            if grep -q 'RESULT fail' <<< $log; then
                __result="true"
            fi
        done
    echo $__result
}

# write_out_monolog
# For tests that have one long log output,
# print the log first, then the results. Results
# are extracted from a module_manifest.json

function write_out_monolog() {
    local _REPORT=$1
    local _MANIFEST=$2
    local _MONO_LOG=$3
    local _RESULT_LINES=$4

    mapfile -t _TEST_ARR < <(jq -r 'keys[]' $_MANIFEST)

    echo $_______REPORT_DIVIDER | tee -a $_REPORT
    cat $_MONO_LOG | tee -a $_REPORT
    echo | tee -a $_REPORT

    for test_name in "${_TEST_ARR[@]}";
        do
            test_desc="$(jq --arg tn "$test_name" -r '.[$tn].desc' $_MANIFEST)"

            write_out_result $_REPORT \
                            "$test_name" \
                            "$test_desc" \
                            "See log above" \
                            "$(grep "RESULT.*$test_name" $_RESULT_LINES)"
        done
}