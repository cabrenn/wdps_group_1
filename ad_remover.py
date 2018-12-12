import cssselect
import requests

class AdRemover(object):
    def __init__(self):
        rule_urls = [
        'https://easylist-downloads.adblockplus.org/ruadlist+easylist.txt',
        'https://filters.adtidy.org/extension/chromium/filters/1.txt'
        ]

        rules_files = [url.rpartition('/')[-1] for url in rule_urls]

        # download files containing rules
        for rule_url, rule_file in zip(rule_urls, rules_files):
            r = requests.get(rule_url)
            with open(rule_file, 'w') as f:
                print(r.text, file=f)

        if not rules_files:
            raise ValueError("one or more rules_files required")

        translator = cssselect.HTMLTranslator()
        rules = []

        for rules_file in rules_files:
            with open(rules_file, 'r') as f:
                for line in f:
                    # elemhide rules are prefixed by ## in the adblock filter syntax
                    if line[:2] == '##':
                        try:
                            rules.append(translator.css_to_xpath(line[2:]))
                        except cssselect.SelectorError:
                            # just skip bad selectors
                            pass

        # create one large query by joining them the xpath | (or) operator
        self.xpath_query = '|'.join(rules)

    def remove_ads(self, tree):
        """Remove ads from an lxml document or element object.

        The object passed to this method will be modified in place."""

        for elem in tree.xpath(self.xpath_query):
            elem.getparent().remove(elem)


