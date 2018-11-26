import nltk
import warc
import spacy
from bs4 import BeautifulSoup
from nltk.corpus import wordnet
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from spacy.lemmatizer import Lemmatizer
nlp = spacy.load('en')
from spacy.lang.en import LEMMA_INDEX, LEMMA_EXC, LEMMA_RULES

def strip_http_headers(http_reply):
    """ Removes the HTTP response headers from http_reply byte-array """
    p = http_reply.find(b'\r\n\r\n')
    if p >= 0:
        return http_reply[p+4:]
    return http_reply


if __name__ == '__main__':

    f = warc.open('sample.warc.gz')

    first_record = True

    for record in f:
        # skip the first record (only contains information about the WARC file,
        # no HTML)
        if first_record:
            first_record = False
            continue

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

        # Generate tokens
        tokens = nltk.word_tokenize(page_text)

        # Continue here doing something with the tokens...
        print(tokens)

        # Lemmatization using Spacy
        #lem = Lemmatizer()
        #lem = Lemmatizer(LEMMA_INDEX, LEMMA_EXC, LEMMA_RULES)
        #for w in tokens:
        #    tokens1 = nlp(w)
        #    #tokens_lem = tokens1.lower()
        #    print ("Actual:%s Lemma: %s" % (w, lem(u'tokens1')))

        # Lemmatization using NLTK
        lem = WordNetLemmatizer()
        for w in tokens:
            tokens_lem = w.lower()
            lemmatized_tokens = lem.lemmatize(tokens_lem)
            #print ("Actual:%s Lemma: %s" % (w, lemmatized_tokens))

        # Stemming with Porter
        #porter_stemmer = PorterStemmer()
        #for w in tokens:
            #print("Actual: %s Stem: %s" %(w, porter_stemmer.stem(w)))

        # Defining the English stopwords
        stop_words = set(stopwords.words('english'))

        # Removing the stopwords from the list of tokens
        filtered_tokens = []
        for w in tokens:
            tokens_stop = w.lower()
            if tokens_stop not in stop_words:
                filtered_tokens.append(w)
        print(filtered_tokens)
