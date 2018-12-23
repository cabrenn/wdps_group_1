import requests
import sys

MAX_IDS = 10

class EsApi:
    def __init__(self, node, port, sparql_api):
        self.node = node
        self.port = port
        self.sparql_api = sparql_api
        self.n_top_hits = 50

    def query(self, query):
        url = 'http://{}:{}/freebase/label/_search'.format(self.node, self.port)
        try:
            response = requests.get(url, params={'q': query, 'size': self.n_top_hits})
        except requests.exceptions.Timeout:
            print("ElasticSearch API timed out. Is ElasticSearch running?")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print("ElasticSearch API failed. Exception caught [{}]".format(e))
            sys.exit(1)
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

    def get_fb_id(self, entity, entity_label):
        url = 'http://{}:{}/freebase/label/_search'.format(self.node, self.port)
        try:
            response = requests.get(url, params={'q': entity, 'size': self.n_top_hits})
        except requests.exceptions.Timeout:
            print("ElasticSearch API timed out. Is ElasticSearch running?")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print("ElasticSearch API failed. Exception caught [{}]".format(e))

        if response:
            response = response.json()
            max_score = response.get('hits',{}).get('max_score')
        
            hits = response.get('hits', {}).get('hits', [])

            scores = []

            i = 0
            for hit in hits:
                if i > MAX_IDS:
                    break
                freebase_label = hit.get('_source', {}).get('label')
                freebase_id = hit.get('_source', {}).get('resource')
                if len(freebase_id) < 4:
                    continue

                wiki_cosim = self.sparql_api.wiki_title_cosim(freebase_id[1:].replace("/","."), entity)
                if wiki_cosim > 0.7:
                    return freebase_id

                #calc label matches
                match_score = self.sparql_api.label_match_score(freebase_id[1:].replace("/","."), entity_label)
                scores.append((freebase_id, match_score))
                i += 1

            scores = sorted(scores, key=lambda x: x[1], reverse=True)
            if len(scores) == 0:
                return
            max_score = scores[0][1]
            # if max_score == 0:
            #     return

            top_candidates = []

            for s in scores:
                if s[1] != max_score:
                    break
                curr_n_rels = self.sparql_api.query(freebase_id[1:].replace("/","."))
                top_candidates.append((s[0], curr_n_rels))

            if len(top_candidates) == 1:
                return top_candidates[0][0]
            else:
                return sorted(top_candidates, key=lambda x: x[1], reverse=True)[0][0]

