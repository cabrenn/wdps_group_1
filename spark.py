import warc
import spacy
import sys
import subprocess
import requests
import pycld2
from io import BytesIO
from bs4 import BeautifulSoup
from spacy.lang.en import English
from spacy.tokenizer import Tokenizer
from spacy.lemmatizer import Lemmatizer
from spacy.pipeline import Tagger
from spacy_cld import LanguageDetector
from spacy.pipeline import DependencyParser
import collections


DOMAIN sys.argv[1]

# https://spacy.io/usage/linguistic-features#entity-types
ALLOWED_ENTITY_TYPES = ['PERSON', 'NORP', 'FAC', 'ORG', 'GPE', 'LOC',
                        'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW']


def search(domain, query):
    url = 'http://%s/freebase/label/_search' % domain
    response = requests.get(url, params={'q': query, 'size':1})
    id_labels = {}
    if response:
        response = response.json()
        for hit in response.get('hits', {}).get('hits', []):
            # print(hit)
            freebase_label = hit.get('_source', {}).get('label')
            freebase_id = hit.get('_source', {}).get('resource')

            # url2 = 'http://%s/freebase/m/_search' % domain
            # res2 = requests.get(url2, params={'q': freebase_id, 'size':5})
            # print(res2.json())
            id_labels.setdefault(freebase_id, set()).add( freebase_label )
    return id_labels

def strip_http_headers(http_reply):
    """ Removes the HTTP response headers from http_reply byte-array """
    p = http_reply.find(b'\r\n\r\n')
    if p >= 0:
        return http_reply[p+4:]
    return http_reply


def strip_whitespace(text):
    """ removes whitespace from a given text. """
    new_text = ''
    for w in text.split():

        tmp = w.strip(' \t\n\r') + ' '
        if not len(tmp) == 0:
            new_text += tmp

    return new_text


def create_freebase_ids(html):
    if not html[1]:
        return
    else:
        pass
        # print("HTML: [" + html[1] + "]")
    nlp = spacy.load('en')
    language_detector = LanguageDetector()
    nlp.add_pipe(language_detector)
    
    f = warc.WARCFile(fileobj=BytesIO(("WARC/1.0" + html[1]).encode('utf-8')))
    # nlp = spacy.load('en', disable=['parser', 'ner'])
    
    for record in f:
        if not record:
            continue
        # The document ID corresponding to this record
        document_id = html[0]

        # if not document_id.endswith('091'):
        #     continue

        # Removes HTTP header from the WARC records
        html = strip_http_headers(record.payload.read())

        # HTML parser
        soup = BeautifulSoup(html.decode('utf-8', 'ignore'), 'html.parser')

        # Removes script / style tags from the HTML
        # (For some reason they get reconized as text)
        for script in soup(['script', 'style']):
            script.decompose()

        # Extract just the text from the HTML
        page_text = strip_whitespace(soup.get_text())


        # Generate tokens with Spacy
        try:
            document = nlp(page_text)
        except pycld2.error as e:
            continue

        # Check for English content
        if 'en' in document._.language_scores:
            if page_text and document._.language_scores['en'] < 0.90:
                continue

        if document.is_parsed:
            # for chunk in document.noun_chunks:
            #     print(document_id, '\t', chunk.text)
            for e in document.ents:
                if not e.text.isspace():
                    for fb_id, labels in search(DOMAIN, e.text).items():
                        yield(document_id, '\t', e.text, '\t', fb_id)
                        break
        break
    
sc = SparkContext("yarn", "wdps1801")
    
#HDFS_ROOT = "/home/peteru/Documents/jupyter/"
#KEYNAME = "WARC-TREC-ID"
OUTFILE = "outfile"

rdd = sc.newAPIHadoopFile("sample.warc.gz", #HDFS_ROOT + "sample.warc.gz",
    "org.apache.hadoop.mapreduce.lib.input.TextInputFormat",
    "org.apache.hadoop.io.LongWritable",
    "org.apache.hadoop.io.Text",
    conf={"textinputformat.record.delimiter": "WARC/1.0"})

rdd = rdd.flatMap(create_freebase_ids)

rdd = rdd.saveAsTextFile(OUTFILE)
