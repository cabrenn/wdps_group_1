from os import path
from pyspark import SparkContext
import sys
import spacy
from spacy_cld import LanguageDetector
import es_api as es
import sparql_api as sparql
import entity_linker as el
import ad_remover as ad_remover
from subprocess import getoutput

import logging
logging.basicConfig(filename='log_spark.txt',level=logging.INFO)
logging.basicConfig(format='%(asctime)s %(message)s')


def main():
    input_folder = sys.argv[5]
    output_folder = sys.argv[6]
    sparql_api = sparql.SparqlApi(sys.argv[3], sys.argv[4])
    es_api = es.EsApi(sys.argv[1], sys.argv[2], sparql_api)
    ad_rm_api = ad_remover.AdRemover()
    el_app = el.EntityLinker(es_api, None, ad_rm_api)

    sc = SparkContext("yarn", "wdps1801")

    rdd = sc.newAPIHadoopFile(input_folder,
                              "org.apache.hadoop.mapreduce.lib.input.TextInputFormat",
                              "org.apache.hadoop.io.LongWritable",
                              "org.apache.hadoop.io.Text",
                              conf={"textinputformat.record.delimiter": "WARC/1.0"})
    rdd = sc.parallelize(rdd.take(10))
    rdd = rdd.flatMap(lambda a : el_app.create_freebase_ids_spark(a))
    rdd = rdd.saveAsTextFile(output_folder)
    

if __name__ == '__main__':
    main()
