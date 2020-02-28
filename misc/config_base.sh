# Script file included by all setup scripts to load local config.

LOCAL_SYSTEM=local/system.conf
DEFAULT_CONF=${DAQ_CONF:-misc/system_base.conf}

if [ -d venv ]; then
    echo Activating venv
    source venv/bin/activate
fi

if [ ! -f "$LOCAL_SYSTEM" ]; then
    echo No $LOCAL_SYSTEM found, copying defaults from $DEFAULT_CONF...
    mkdir -p local
    cp $DEFAULT_CONF $LOCAL_SYSTEM
fi

echo Loading config from $LOCAL_SYSTEM into inst/config/system.conf
mkdir -p inst/config
python3 daq/configurator.py $LOCAL_SYSTEM $run_args > inst/config/system.conf
source inst/config/system.conf
