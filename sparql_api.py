import requests

class SparqlApi:
    def __init__(self, node, port):
        self.node = node
        self.port = port

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