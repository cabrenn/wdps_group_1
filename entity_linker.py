import warc
from io import StringIO, BytesIO
from bs4 import BeautifulSoup
import spacy
import re
from spacy_cld import LanguageDetector
import pycld2
from lxml.etree import tostring
import lxml.html
from subprocess import getoutput
import logging
from time import time

# import pycld2

# https://spacy.io/usage/linguistic-features#entity-types
ALLOWED_ENTITY_LABELS = ['PERSON', 'NORP', 'FAC', 'GPE', 'LOC',
                         'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW', 'ORG']
                         #'ORG'





class EntityLinker:
    def __init__(self, es_api, nlp, ad_remover):
        self.es_api = es_api
        self.nlp = nlp
        self.ad_remover = ad_remover
        self.regex_entity_validator = re.compile(r'[’*=&]')

    def is_valid_entity(self, entity):
        ret_found = self.regex_entity_validator.search(entity)
        return not bool(ret_found)

    def skip_first_item(self, iterable_seq):
        seq_it = iter(iterable_seq)
        next(seq_it)
        return iterable_seq

    def is_english_doc(self, doc):
        if 'en' in doc._.language_scores:
            return doc._.language_scores['en'] > 0.90
        return False

    def strip_http_headers(self, http_reply):
        """ Removes the HTTP response headers from http_reply byte-array """
        ret_reply = http_reply  
        p = http_reply.find(b'\r\n\r\n')
        if p >= 0:
            ret_reply = http_reply[p + 4:]
            if len(ret_reply) == 0:
                ret_reply = None
        return ret_reply


    def strip_whitespace(self, text):
        """ removes whitespace from a given text. """
        new_text = ''
        for w in text.split():

            tmp = w.strip(' \t\n\r') + ' '
            if not len(tmp) == 0:
                new_text += tmp

        return new_text

    def create_freebase_ids_spark(self, html):
        try:
            f = warc.WARCFile(fileobj=BytesIO(("WARC/1.0" + html[1]).encode('utf-8')))
            ent = self.get_freebase_ids(next(iter(f)))
            if ent is not None:
                return list(ent)
        except Exception as e:
            if "warc-trec-id" not in str(e):
                return ['warc-trec-id exception: {}'.format(e)]
                raise e
            return ['other exception: {}'.format(e)]
        return ['{}'.format('this shouldnt happen')]

    

    def create_freebase_ids_local(self, input_path, output_path):
        f = warc.open(input_path)
        i = 0
        with open(output_path, 'w') as output_file:
            for record in self.skip_first_item(f):
                time2 = time()
                for entity in self.get_freebase_ids(record):
                    if entity is not None and entity is not '':
                        output_file.write('{}\n'.format(entity))
                i = i+1


    def get_freebase_ids(self, warc_record):
        nlp = spacy.load('en_core_web_sm')
        try:
            language_detector = LanguageDetector()
            nlp.add_pipe(language_detector)
        except:
            pass

        try:  
            document_id = warc_record['WARC-Trec-ID']
        except Exception as e:
            return 'Exception warc: [{}]'.format(e)

        read_record = warc_record.payload.read()
        
        striped_headers = self.strip_http_headers(read_record)
        if striped_headers is None:
            return 'striped_headers is: [{}]'.format(striped_headers)
        
        document = lxml.html.parse(BytesIO(striped_headers))
        try:
            self.ad_remover.remove_ads(document)
        except Exception as e:
            return 'Exception ad_remover: [{}]'.format(e)
        # return ''
        clean_html = tostring(document).decode("utf-8")
       
        # HTML parser
        soup = BeautifulSoup(clean_html, 'html.parser')

        LINK_FILTER_MODIFIER = 5

        for a in soup(['a']):
            if a.parent:
                parent_text = a.parent.get_text()
                if len(parent_text) < LINK_FILTER_MODIFIER * len(a.get_text()):
                    a.decompose()

        for x in soup(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'script', 'style', 'title']):
            x.decompose()

        # Removes script / style tags from the HTML
        # (For some reason they get reconized as text)
        # for script in soup(['script', 'style']):
        #     script.decompose()

        # Extract just the text from the HTML
        page_text = self.strip_whitespace(soup.get_text())

        # Generate tokens with Spacy
        try:
            document = nlp(page_text)
        except pycld2.error as e:
            return 'pycld2 exception: [{}]'.format(e)
        except AttributeError as e:
            if not str(e).startswith('[E047]'):
                raise e
            return 'AttributeError: [{}]'.format(e)

        # Check for English content
        if not self.is_english_doc(document):
            return 'no english doc'

        if document.is_parsed:
            for e in document.ents:
                if e.label_ in ALLOWED_ENTITY_LABELS:
                    if not self.is_valid_entity(e.text):
                        continue
                
                    # fb_id = self.es_api.query(e.text)
                    fb_id = self.es_api.get_fb_id(e.text, e.label_)
                    if not fb_id:
                        continue
                    yield '{}\t{}\t{}'.format(document_id, e.text, fb_id)
