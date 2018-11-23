import nltk
import warc
from bs4 import BeautifulSoup


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
