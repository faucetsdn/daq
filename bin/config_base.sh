# Script file included by all setup scripts to load local config.

if [[ -z $DAQ_LIB ]]; then
    source etc/FILES_MAPPING
fi

LOCAL_YAML=$DAQ_CONF/system.yaml
LOCAL_CONF=$DAQ_CONF/system.conf
DEFAULT_CONF=$DAQ_LIB/config/system/base.yaml
OUT_CONF=$DAQ_RUN/config/system.conf
if [ -z $DAQ_DIR ]; then
    DAQ_DIR=daq
fi

if [ -d venv ]; then
    echo Activating venv
    source venv/bin/activate
fi

if [ ! -f "$LOCAL_YAML" -a ! -f "$LOCAL_CONF" ]; then
    echo No $LOCAL_YAML or $LOCAL_CONF found, pointing at $DEFAULT_CONF...
    mkdir -p $DAQ_CONF 
    echo "include: $DEFAULT_CONF" > $LOCAL_YAML
    conf_file=$LOCAL_YAML
elif [ -f "$LOCAL_YAML" -a -f "$LOCAL_CONF" ]; then
    echo Both $LOCAL_YAML and $LOCAL_CONF found, not sure which to use: panic quit.
    false
elif [ -f "$LOCAL_YAML" ]; then
    conf_file=$LOCAL_YAML
else
    conf_file=$LOCAL_CONF
fi

echo Flattening config from $conf_file into $OUT_CONF
mkdir -p $(dirname $OUT_CONF)
python3 $DAQ_DIR/configurator.py $conf_file $run_args > $OUT_CONF

# Shell variables can't handle dot character, so convert to underscore
echo -n > $OUT_CONF.sh
cat $OUT_CONF | while read line; do
    before=${line%%=*}
    after=${line#*=}
    echo ${before//[.-]/_}=$after >> $OUT_CONF.sh
done

source $OUT_CONF.sh
