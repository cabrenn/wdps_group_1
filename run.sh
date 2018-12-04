# Set variables and set-up virtual environment

export PYTHON=python3.5
export SPARK_HOME=~/scratch/spark-2.4.0-bin-without-hadoop

if [ $1 == "create-env" ]; then
    echo "Setting up Python environemnt..."
    $PYTHON -m venv venv
    source venv/bin/activate
    $PYTHON -m pip install -r requirements.txt
    $PYTHON -m spacy download en
    deactivate

    pushd venv/
    zip -rq ../venv.zip *
    popd
    echo "Python environment set up."
fi

export PYSPARK_PYTHON="venv/bin/python"

PY_LD=$($PYTHON -c 'import sys; print(sys.executable)')
export LD_LIBRARY_PATH="${PY_LD%$"/bin/python"*}/lib"



echo "Initiating ElasticSearch..."
ES_PORT=9200
ES_BIN=/home/bbkruit/scratch/wdps/elasticsearch-2.4.1/bin/elasticsearch

prun -o .es_log -v -np 1 ESPORT=$ES_PORT $ES_BIN </dev/null 2> .es_node &
echo "Waiting 15 seconds for ElasticSearch to set up..."
sleep 15
ES_NODE=$(cat .es_node | grep '^:' | grep -oP '(node...)')
ES_PID=$!
echo "ElasticSearch should be running now on node $ES_NODE:$ES_PORT (connected to process $ES_PID)"



echo "Running entity linking app on spark cluster..."

~/scratch/spark-2.4.0-bin-without-hadoop/bin/spark-submit \
--conf "spark.yarn.appMasterEnv.SPARK_HOME=$SPARK_HOME" \
--conf "spark.yarn.appMasterEnv.PYSPARK_PYTHON=$PYSPARK_PYTHON" \
--conf "spark.executorEnv.LD_LIBRARY_PATH=$LD_LIBRARY_PATH" \
--conf "spark.yarn.appMasterEnv.LD_LIBRARY_PATH=$LD_LIBRARY_PATH" \
--master yarn \
--deploy-mode cluster \
--num-executors 25 \
--executor-cores 2 \
--executor-memory 1GB \
--archives venv.zip#venv \
spark.py $ES_NODE:$ES_PORT

echo "Spark job of entity linking app finished."


echo "Killing ElasticSearch process..."
kill $ES_PID
echo "Killed."
echo "Script finished."
