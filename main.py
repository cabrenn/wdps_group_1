import warc
import spacy
from bs4 import BeautifulSoup
from spacy.lang.en import English
from spacy.tokenizer import Tokenizer
from spacy.lemmatizer import Lemmatizer
from spacy.pipeline import Tagger
from spacy_cld import LanguageDetector
from spacy.pipeline import DependencyParser

def strip_http_headers(http_reply):
    """ Removes the HTTP response headers from http_reply byte-array """
    p = http_reply.find(b'\r\n\r\n')
    if p >= 0:
        return http_reply[p+4:]
    return http_reply


if __name__ == '__main__':

    f = warc.open('sample.warc.gz')
    nlp = spacy.load('en')
    language_detector = LanguageDetector()
    nlp.add_pipe(language_detector)
    first_record = True

    for record in f:
        # skip the first record (only contains information about the WARC file,
        # no HTML)
        if first_record:
            first_record = False
            continue

        # The document ID corresponding to this record
        document_id = record['WARC-Trec-ID']

        # Removes HTTP header from the WARC records
        html = strip_http_headers(record.payload.read())

        # HTML parser
        soup = BeautifulSoup(html.decode('utf-8', 'ignore'), 'html.parser')

        # Removes script / style tags from the HTML
        # (For some reason they get reconized as text)
        for script in soup(['script', 'style']):
            script.decompose()

        # Extract just the text from the HTML
        page_text = soup.get_text()

        # Generate tokens with Spacy
        document = nlp(page_text)
        # Check for English content
        if page_text and document._.language_scores['en'] < 0.90:
            continue
        # Lemmatization and POS Tagging with Spacy
        # for w in document:
        #     print(w, ":", w.lemma_ , ",", w.tag_)
        # Dependency Parsing
        parser = DependencyParser(nlp.vocab)
        processed = parser(document)
        print(processed)




        # def represent_word(word):
        #     text = word.text
        #     # True-case, i.e. try to normalize sentence-initial capitals.
        #     # Only do this if the lower-cased form is more probable.
        #     if text.istitle() and is_sent_begin(word) \
        #     and word.prob < word.doc.vocab[text.lower()].prob:
        #         text = text.lower()
        #     return text + '|' + word.tag_

        ## Defining the English stopwords
        # stop_words = set(stopwords.words('english'))
        #
        ## Removing the stopwords from the list of tokens
        # filtered_tokens = []
        # for w in document:
        #     tokens_stop = w.lower()
        #     if tokens_stop not in stop_words:
        #         filtered_tokens.append(w)
