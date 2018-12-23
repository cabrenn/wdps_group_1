import requests
from difflib import SequenceMatcher

class SparqlApi:
    def __init__(self, node, port):
        self.node = node
        self.port = port

        self.label_matches = {'PERSON': ['people.person'],
                              'NORP': ['religion.deity', 'relligion.religion', 'government.political_district', 'government.political_party'],
                              'FAC': ['architecture.structure'],
                              'ORG': ['organization.organization'],
                              'GPE': ['location.country', 'location.citytown'],
                              'LOC': ['geography.body_of_water', 'geography.geographical_feature', 'geography.island'],
                              'PRODUCT': ['business.product_category', 'business.product_line'],
                              'EVENT': ['time.event', 'time.recurring_event', 'base.culturalevent.event'],
                              'WORK_OF_ART': ['music.album', 'music.artist', 'music.genre', 'book.magazine',
                                              'book.newspaper', 'book.publication', 'book.published_work', 'film.film'],
                              'LAW': ['law.invention', 'law.court_jurisdiction_area']}

    def query(self, query):
        url = 'http://{}:{}/sparql'.format(self.node, self.port)
        response = requests.post(url, data={
            'print': True, 
            'query': 'select ?p WHERE {<http://rdf.freebase.com/ns/%s> ?p ?o}' % query
            })
        n_results = 0
        if response:
            try:
                response = response.json()
                n_results = response.get('stats', {}).get('nresults')
                if n_results is None:
                    n_results = 0
                else:
                    n_results = int(n_results)
            except Exception as e:
                print(response)
                raise e

        return n_results


    def label_match_score(self, fb_id, label):
        url = 'http://{}:{}/sparql'.format(self.node, self.port)
        response = requests.post(url, data={
            'print': True, 
            'query': 'select ?o WHERE {<http://rdf.freebase.com/ns/%s> <http://rdf.freebase.com/ns/type.object.type> ?o}' % fb_id
        })

        score = 0
        if response:
            try:
                response = response.json()
                bindings = response.get('results').get('bindings')
                for b in bindings:
                    object_type = b.get('o', {}).get('value').split('/')[-1]
                    if object_type in self.label_matches[label]:
                        score += 1

            except Exception as e:
                print(response)
                raise e

        return score


    def wiki_title_cosim(self, fb_id, entity_name):
        url = 'http://{}:{}/sparql'.format(self.node, self.port)
        response = requests.post(url, data={
            'print': True, 
            'query': 'select ?o WHERE {<http://rdf.freebase.com/ns/%s> <http://rdf.freebase.com/key/wikipedia.en_title> ?o}' % fb_id
        })

        if response:
            try:
                response = response.json()
                bindings = response.get('results').get('bindings')
                cosim = 0

                for b in bindings:
                    wiki_title = b.get('o', {}).get('value')
                    tmp = SequenceMatcher(None, wiki_title.lower(), entity_name.lower()).ratio()
                    if tmp > cosim:
                        cosin = tmp

            except Exception as e:
                print(response)
                raise e
            return cosim
            
        else:
            return 0



