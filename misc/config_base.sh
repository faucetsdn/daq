# Script file included by all setup scripts to load local config.

LOCAL_SYSTEM=local/system.conf
DEFAULT_CONF=${DAQ_CONF:-misc/system_base.conf}

run_mode=$(cat misc/RELEASE_VERSION)

if [ ! -f "$LOCAL_SYSTEM" -a -z "$DONT_MAKE_LOCAL" ]; then
    echo No $LOCAL_SYSTEM found, copying defaults from $DEFAULT_CONF...
    mkdir -p local
    cp $DEFAULT_CONF $LOCAL_SYSTEM
fi

echo Loading config from $LOCAL_SYSTEM
eval $(python3 daq/configurator.py $LOCAL_SYSTEM $run_args)
