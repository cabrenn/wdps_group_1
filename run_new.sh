#!/bin/bash
# Set variables and set-up virtual environment

ES_BIN=$(realpath ~/scratch/elasticsearch-2.4.1/bin/elasticsearch)
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
KB_BIN=/home/bbkruit/scratch/trident/build/trident
KB_PATH=/home/jurbani/data/motherkb-trident
prun -o .kb_log -v -np 1 $KB_BIN server -i $KB_PATH --port $KB_PORT </dev/null 2> .kb_node &
echo "Waiting for Sparql to prepare node..."
sleep 5
KB_NODE=$(cat .kb_node | grep '^:' | grep -oP '(node...)')
KB_PID=$!
echo "Trident should be running now on node $KB_NODE:$KB_PORT (connected to process $KB_PID)"

python main-local.py $ES_NODE $ES_PORT $KB_NODE $KB_PORT

echo "Killing ElasticSearch and Sparql process..."
kill $ES_PID
kill $KB_PID
echo "Killed."
echo "Script finished."
