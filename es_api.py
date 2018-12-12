import requests

class EsApi:
    def __init__(self, node, port, sparql_api):
        self.node = node
        self.port = port
        self.sparql_api = sparql_api
        self.n_top_hits = 50

    def query(self, query):
        url = 'http://{}:{}/freebase/label/_search'.format(self.node, self.port)
        response = requests.get(url, params={'q': query, 'size': self.n_top_hits})
        n_rels = 0
        top_fb_id = ""
        id_labels = {}
        if response:
            response = response.json()
            max_score = response.get('hits',{}).get('max_score')
            for hit in response.get('hits', {}).get('hits', []):
                if hit.get('_score') != max_score:
                    continue
                freebase_label = hit.get('_source', {}).get('label')
                freebase_id = hit.get('_source', {}).get('resource')
                if len(freebase_id) < 4:
                    continue
                id_labels.setdefault(freebase_id, set()).add(freebase_label)
                curr_n_rels = self.sparql_api.query(freebase_id[1:].replace("/","."))
                if curr_n_rels > n_rels or not top_fb_id:
                    top_fb_id = freebase_id
                    n_rels = curr_n_rels
        return top_fb_id