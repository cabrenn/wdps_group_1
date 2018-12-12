from os import path
import sys
import spacy
from spacy_cld import LanguageDetector
import es_api as es
import sparql_api as sparql
import entity_linker as el
import ad_remover as ad_remover

HDFS_ROOT = "/user/wdps1801/"
OUTPUT_FOLDER = "freebase_ids"

'''TODO
    - make sparql better
'''


def main():
    sparql_api = sparql.SparqlApi(sys.argv[3], sys.argv[4])
    es_api = es.EsApi(sys.argv[1], sys.argv[2], sparql_api)
    ad_rm_api = ad_remover.AdRemover()
    spacy_nlp = spacy.load('en_core_web_sm')
    # nlp = spacy.load('en', disable=['parser', 'ner'])
    language_detector = LanguageDetector()
    spacy_nlp.add_pipe(language_detector)
    el_app = el.EntityLinker(es_api, spacy_nlp, ad_rm_api)
    el_app.create_freebase_ids_local('sample.warc.gz', '{}/out.txt'.format(OUTPUT_FOLDER))

if __name__ == '__main__':
    main()
