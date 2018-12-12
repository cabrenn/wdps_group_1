from os import path
from pyspark import SparkContext
import sys
import spark
import spacy
import es_api as es
import sparql_api as sparql
import entity_linker as el
import ad_remover as ad_remover

HDFS_ROOT = "/user/wdps1801/"
OUTPUT_FOLDER = "freebase_ids"

'''TODO
	- KEYNAME = "WARC-TREC-ID"(document IDs)
	- language check
'''


def main():
    sparql_api = sparql.SparqlApi(sys.argv[3], sys.argv[4])
    es_api = es.EsApi(sys.argv[1], sys.argv[2], sparql_api)
    ad_rm_api = ad_remover.AdRemover()
    spacy_nlp = spacy.load('en_core_web_sm')
    # nlp = spacy.load('en', disable=['parser', 'ner'])
    # language_detector = LanguageDetector()
    # nlp.add_pipe(language_detector)
    el_app = el.EntityLinker(es_api, spacy_nlp, ad_rm_api)

    sc = SparkContext("yarn", "wdps1801")

    rdd = sc.newAPIHadoopFile(path.join(HDFS_ROOT, "sample.warc.gz"),
                              "org.apache.hadoop.mapreduce.lib.input.TextInputFormat",
                              "org.apache.hadoop.io.LongWritable",
                              "org.apache.hadoop.io.Text",
                              conf={"textinputformat.record.delimiter": "WARC/1.0"})

    rdd = sc.parallelize(rdd.take(50))
    rdd = rdd.flatMap(el_app.create_freebase_ids_spark)
    rdd = rdd.saveAsTextFile(path.join(HDFS_ROOT, OUTPUT_FOLDER))


if __name__ == '__main__':
    main()
