import warc
from io import StringIO, BytesIO
from bs4 import BeautifulSoup
import spacy
import re
from lxml.etree import tostring
import lxml.html

# import pycld2

# https://spacy.io/usage/linguistic-features#entity-types
ALLOWED_ENTITY_LABELS = ['PERSON', 'NORP', 'FAC', 'GPE', 'LOC',
                         'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW']
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
        if not html[1]:
            return
        f = warc.WARCFile(fileobj=StringIO(b'WARC/1.0' + html[1]))
        yield self.get_freebase_ids(f.next())

    def skip_first_item(self, iterable_seq):
        seq_it = iter(iterable_seq)
        next(seq_it)
        return iterable_seq

    def create_freebase_ids_local(self, input_path, output_path):
        f = warc.open(input_path)
        i = 0
        with open(output_path, 'w') as output_file:
            for record in self.skip_first_item(f):
                for entity in self.get_freebase_ids(record):
                    if entity is not None:
                        output_file.write('{}\n'.format(entity))
                i = i+1
                if i > 20:
                    break
            
    

    def get_freebase_ids(self, warc_record):
        # The document ID corresponding to this record
        document_id = warc_record['WARC-Trec-ID']
        print(document_id)
        #print(document_id)

        read_record = warc_record.payload.read()
        
        # Removes HTTP header from the WARC records
        striped_headers = self.strip_http_headers(read_record)
        if striped_headers is None:
            return

        document = lxml.html.parse(BytesIO(striped_headers))
        try:
            self.ad_remover.remove_ads(document)
        except:
            #print("[{}]".format(document))
            #print("[{}]".format(read_record))
            #print("[{}]".format(len(read_record)))
            #print("[{}]".format(len(striped_headers)))
            return

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
            document = self.nlp(page_text)
        except pycld2.error as e:
            return

        # Check for English content
        if not self.is_english_doc(document):
            return

        if document.is_parsed:
            for e in document.ents:
                if e.label_ in ALLOWED_ENTITY_LABELS:
                    if not self.is_valid_entity(e.text):
                        continue
                
                    fb_id = self.es_api.query(e.text)
                    if not fb_id:
                        continue
                    yield '{}\t{}\t{}'.format(document_id, e.text, fb_id)
