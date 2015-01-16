'''
Created on Aug 30, 2014

@author: rmn
'''
import codecs
from hashlib import md5
import json
import jsonrpclib
import os
import re
import simplejson
import sys
#import MBSP

from cache import CachingDecorator, cache_file
from common import hash_file, prep_for_json


class Extract_NLP_Tags(object):

    """
    Class for extracting NLP information such as POS, coref, parsetree, etc from input
    """

    def _extract_NP(self, text, mode='simple'):
        parse_tree = text

        def fun(d):
            if 'NP' in d:
                yield d['NP']
            for k in d:
                if isinstance(d[k], list):
                    for i in d[k]:
                        for j in fun(i):
                            yield j

        def fun1(d):
            out = []
            if isinstance(d, list):
                for i in d:
                    out.append(fun1(i))
            elif isinstance(d, dict):
                val = d[d.keys()[0]]
                if isinstance(val, list):
                    return fun1(val)
                else:
                    return d[d.keys()[0]]
            return out

        def flattened_list_and_sublists(l):
            # First return value is l, flattened.
            # Second return value is a list of flattened forms of all nested sublists
            # of l.

            flattened = []
            flattened_sublists = []

            for i in l:
                if isinstance(i, list):
                    i_flattened, i_flattened_sublists = flattened_list_and_sublists(
                        i)
                    flattened += i_flattened
                    flattened_sublists.append(i_flattened)
                    flattened_sublists += i_flattened_sublists
                else:
                    flattened.append(i)
            return flattened, flattened_sublists

        def all_flattened_sublists(l):
            l_flattened, l_sublists_flattened = flattened_list_and_sublists(l)
            return l_sublists_flattened

        def flatten(S):
            if S == []:
                return S
            if isinstance(S[0], list):
                return flatten(S[0]) + flatten(S[1:])
            return S[:1] + flatten(S[1:])

        def extract_lists(S):
            out = []
            s = S[0]
            i = 0
            for s in S:
                if isinstance(s, list):
                    out.append(extract_lists(s))
                else:
                    out.append(s)
            return out

        def fun2(S):
            out = []
            for item in S:
                if isinstance(item, list):
                    out.append(flatten(item))

        nps = list(fun(parse_tree))
        if mode == 'detailed':
            return nps
        if mode == 'detailed_flattened':
            return all_flattened_sublists(nps)
        if mode == 'simple':
            return fun1(nps)
        if mode == 'flattened':
            return all_flattened_sublists(fun1(nps))

    def extract_NP(self, text, mode='simple'):
        """
        Extract noun phrases from a given `text`
        :arg    mode = simple : extracts consecutive terms forming a noun phrase
                mode = detailed: extracts a list of terms and their POS tag in a NP
                mode = flattened: flat list of terms

        Returns a list of Noun Phrases
        """

        parse_trees = self.extract_nlp(text)['parsetree']
        out = [self._extract_NP(e, mode=mode) for e in parse_trees]
        return out

    def parse_parsetree(self, text):
        a = text.replace(':',
                         '##COLON##').replace(',',
                                              '##COMMA##').replace('\\', '\\\\').\
            replace(') (', '),(').replace(
            ' ', ':').replace('(', '{').replace(')', '}')
        a = re.sub(r'([^}:{,]+)', '"\g<1>"', a)
        a = a.replace('##COMMA##', ',').replace('##COLON##', ':')
        b = ''
        s = []
        for i in range(len(a) - 1):
            if a[i:i + 2] == ':{':
                b += ':['
                s.append('#')
                i += 1
            elif a[i:i + 2] == '}}':
                b += '}]'
                i += 1
            elif i == len(a):
                b += '}'
            else:
                b += a[i]
        b = b + '}'
        return json.loads(b)

    def extract_nlp_batch(self, input_list):
        """
        Extract NLP information from `input_list`

        Returns a <dict> {`sentences<list>`: nlp info,
                          `corefs<list>`: coreference info}
                      `sentences` is a list of nlp info corresponding to entries in `input_list`
                       See method *parse* for more info
        """
        digest_data = 'nlptags_batch.cache_' + \
            md5(str(input_list).encode('ascii', 'ignore')).hexdigest()

        if not os.path.exists(self.cachedir):
            print >> sys.stderr, '[cache error] directory %s does not exists' % self.cachedir
            try:
                print '[cache info] Creating caches directory'
                os.makedirs(self.cachedir)
            except:
                print >> sys.stderr, '[cache error] Failed to create caches directory'
                sys.exit(1)
        cache_path = os.path.join(self.cachedir, digest_data)
        if os.path.exists(cache_path):
            with codecs.open(cache_path, mode='rb', encoding='utf-8') as f:
                return json.load(f)
        else:
            nlptags = []
            corefs = []
            for i in input_list:
                parsed = self.parse(i)
                nlptags.append(parsed['sentences'])
                corefs.append(parsed['coref'])
            res = prep_for_json(
                {'sentences': nlptags, 'corefs': corefs})
            with codecs.open(cache_path, mode='wb', encoding='utf-8') as f:
                json.dump(out, f)
            return res

    def parse(self, text):
        """
        Parses sentences in text

        :arg text: sentences
        returns <dict>{'coref': <list>, 'sentences': <list>}
            This dictionary contains the keys sentences and coref.
            The key sentences contains a list of dictionaries for each
            sentence, which contain `parsetree`, `text` and `words`, 
            containing information about parts of speech, recognized named-entities, etc
        """
        return simplejson.loads(self.server.parse(text))

    def extract_nlp(self, text):
        digest_data = 'nlptags.cache_' + \
            md5(text.encode('ascii', 'ignore')).hexdigest()

        if not os.path.exists(self.cachedir):
            print >> sys.stderr, '[cache error] directory %s does not exists' % self.cachedir
            try:
                print '[cache info] Creating caches directory'
                os.makedirs(self.cachedir)
            except:
                print >> sys.stderr, '[cache error] Failed to create caches directory'
                sys.exit(1)
        cache_path = os.path.join(self.cachedir, digest_data)
        if os.path.exists(cache_path):
            with codecs.open(cache_path, mode='rb', encoding='utf-8') as f:
                return json.load(f)
        else:
            nlptags = []
            words = []
            parsed = simplejson.loads(self.server.parse(text))
            for st in parsed['sentences']:
                nlptags.append(self.parse_parsetree(st['parsetree']))
                words.append(st['words'])
            out = prep_for_json({'parsetree': nlptags, 'words': words})
            with codecs.open(cache_path, mode='wb', encoding='utf-8') as f:
                json.dump(out, f)
            return out

    def __init__(self, cachedir='cache',
                 corenlp_server="http://localhost:8083"):
        """
        Connect to the server
        """
        self.server = jsonrpclib.Server(corenlp_server)
        self.cachedir = cachedir


if __name__ == '__main__':
    e = Extract_NLP_Tags()
    obj = json.loads('{"ROOT":[{"S":[{"NP":[{"DT":"This"}]},{"VP":[{"VBZ":"is"},{"NP":[{"NP":[{"DT":"a"},{"JJ":"great"},{"JJ":"non-trivial"},{"NN":"program"}]},{"VP":[{"VBN":"ran"},{"PP":[{"IN":"by"},{"NP":[{"PRP":"me"}]}]}]}]}]}]}]}'
                     )
    i = 0
    tst = {"ROOT": [{"DT": "This"}]}
    from collections import defaultdict
#     out = defaultdict()
    out = {}

    def fun(element):
        for k in element.keys():
            if k not in out:
                out[k] = []
            if isinstance(element[k], list):
                for idx in range(len(element[k])):
                    if isinstance(element[k][idx], dict) and len(element[k][idx]) == 1 and isinstance(element[k][idx][element[k][idx].keys()[0]], str):
                        global i
                        element[k][idx][element[k][idx].keys()[0]] = element[k][idx][
                            element[k][idx].keys()[0]] + '-' + str(i)
                        i += 1
#                         if element[k][idx] not in out[k]:
#                             out[k][idx] = {}
#                         for key in element[k][idx].keys():
#                             element[k][idx][key] = element[k][idx][key] + '-' + i
#                             out[k][idx][key] = element[k][idx][key] + '-' + i
                    elif isinstance(element[k][idx], dict) and len(element[k][idx]) == 1 and isinstance(element[k][idx][element[k][idx].keys()[0]], list):
                        for idx1 in range(len(element[k][idx][element[k][idx].keys()[0]])):
                            fun((element[k][idx][element[k][idx].keys()[0]])[
                                idx1])
                    elif isinstance(element[k][idx], dict) and len(element[k][idx]) > 1:
                        for key2 in element[k][idx]:
                            fun(element[k][idx][key2])
                    elif isinstance(element[k][idx], list):
                        fun(element[k][idx])
    fun(obj)
    print obj
#     print e._extract_NP(obj, mode='flattened')
