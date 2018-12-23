#!/bin/bash

# Set variables and set-up virtual environment
export PYTHON=python3.5
export SPARK_HOME=/home/wdps1801/scratch/libs/spark-2.4.0-bin-without-hadoop
ES_BIN=$(realpath ~/scratch/elasticsearch-2.4.1/bin/elasticsearch)
KB_BIN=/home/bbkruit/scratch/trident/build/trident
KB_PATH=/home/jurbani/data/motherkb-trident

infile="$1"
outfile="$2"


POSITIONAL=()
CREATE_ENV=false
RUN_SPARK=false
RUN_LOCAL=false
while [[ $# -gt 0 ]]
do
key="$3"

case $key in
    -c|--create-env)
    CREATE_ENV=true
    shift # past argument
    # shift # past value
    ;;
    -s|--spark)
    RUN_SPARK=true
    shift # past argument
    # shift # past value
    ;;
    -l|--local)
    RUN_LOCAL=true
    shift # past argument
    # shift # past value
    ;;
    --default)
    DEFAULT=YES
    shift # past argument
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

if [[ -n $1 ]]; then
    echo "Last line of file specified as non-opt/last argument:"
    tail -1 "$1"
fi




if $CREATE_ENV; then
    echo "Setting up Python environemnt..."
    $PYTHON -m venv venv
    source venv/bin/activate
    $PYTHON -m pip install -r requirements.txt
    $PYTHON -m spacy download en_core_web_sm
    deactivate

    pushd venv/
    zip -rq ../venv.zip *
    popd
    echo "Python environment set up."
fi

export PYSPARK_PYTHON="venv/bin/python"

PY_LD=$($PYTHON -c 'import sys; print(sys.executable)')
export LD_LIBRARY_PATH="${PY_LD%$"/bin/python"*}/lib:$LD_LIBRARY_PATH"


echo "Initiating ElasticSearch..."
ES_PORT=9200
prun -o .es_log -v -np 1 ESPORT=$ES_PORT $ES_BIN </dev/null 2> .es_node &
echo "Waiting for ElasticSearch to prepare node..."
until [ -n "$ES_NODE" ]; do ES_NODE=$(cat .es_node | grep '^:' | grep -oP '(node...)'); done
ES_PID=$!
until [ -n "$(cat .es_log* | grep YELLOW)" ]; do sleep 1; done
echo "ElasticSearch should be running now on node $ES_NODE:$ES_PORT (connected to process $ES_PID)"


echo "Initiating Sparql..."
KB_PORT=9090
prun -o .kb_log -v -np 1 $KB_BIN server -i $KB_PATH --port $KB_PORT </dev/null 2> .kb_node &
echo "Waiting for Sparql to prepare node..."
until [ -n "$KB_NODE" ]; do KB_NODE=$(cat .kb_node | grep '^:' | grep -oP '(node...)'); done
# sleep 5
# KB_NODE=$(cat .kb_node | grep '^:' | grep -oP '(node...)')
KB_PID=$!
echo "Trident should be running now on node $KB_NODE:$KB_PORT (connected to process $KB_PID)"


if $RUN_SPARK ; then
    echo "Running entity linking app on spark cluster..."

    $SPARK_HOME/bin/spark-submit \
    --conf "spark.yarn.appMasterEnv.SPARK_HOME=$SPARK_HOME" \
    --conf "spark.yarn.appMasterEnv.PYSPARK_PYTHON=$PYSPARK_PYTHON" \
    --conf "spark.executorEnv.LD_LIBRARY_PATH=$LD_LIBRARY_PATH" \
    --conf "spark.yarn.appMasterEnv.LD_LIBRARY_PATH=$LD_LIBRARY_PATH" \
    --master yarn \
    --deploy-mode client \
    --num-executors 16 \
    --executor-cores 2 \
    --executor-memory 1GB \
    --py-files es_api.py,sparql_api.py,entity_linker.py,ad_remover.py \
    --archives venv.zip#venv \
    main-spark.py $ES_NODE $ES_PORT $KB_NODE $KB_PORT $infile $outfile

    echo "Spark Entity Linking done."
fi

if $RUN_LOCAL; then
    echo "Running entity linking app locally..."
    source venv/bin/activate
    $PYTHON main-local.py $ES_NODE $ES_PORT $KB_NODE $KB_PORT
    deactivate
    echo "Local job finished."
fi

echo "Killing ElasticSearch and Sparql process..."
kill $ES_PID
kill $KB_PID
echo "Killed."
echo "Script finished."
