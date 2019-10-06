# Script file included by all setup scripts to load local config.

LOCAL_SYSTEM=local/system.conf
DEFAULT_CONF=${DAQ_CONF:-misc/system_base.conf}
INST_SYSTEM=inst/config/system.conf

if [ -d venv ]; then
    echo Activating venv
    source venv/bin/activate
fi

run_mode=$(cat misc/RELEASE_VERSION)

if [ ! -f "$LOCAL_SYSTEM" -a "$DONT_MAKE_LOCAL" ]; then
    echo Skipping $LOCAL_SYSTEM install b/c no-local mode.
else
    if [ ! -f "$LOCAL_SYSTEM" ]; then
        echo No $LOCAL_SYSTEM found, copying defaults from $DEFAULT_CONF...
        mkdir -p local
        cp $DEFAULT_CONF $LOCAL_SYSTEM
    fi

    if [ $LOCAL_SYSTEM -nt $INST_SYSTEM ]; then
        echo Loading config from $LOCAL_SYSTEM into $INST_SYSTEM
        mkdir -p ${INST_SYSTEM%/*}
        python3 daq/configurator.py $LOCAL_SYSTEM $run_args > $INST_SYSTEM
    fi
    source inst/config/system.conf
fi
