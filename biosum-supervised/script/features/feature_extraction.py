'''
Created on Feb 4, 2015

@author: rmn
'''
from util.common import tokenize
from util.es_interface import ESInterface
import math
from nltk.tokenize.regexp import RegexpTokenizer
reg_tok = RegexpTokenizer('[^\w\-\']+', gaps=True)


def BM25(query, document, idf_index, stem=True, no_stopwords=True):
    es_int1 = ESInterface(index_name=idf_index)
    terms = list(set([w for w in tokenize(
        query + ' ' + document, no_stopwords=no_stopwords, stem=stem)]))
    count_total = es_int1.count(query='*:*')
    counts = [(w, es_int1.count(w)) for w in terms]
    idfs = {t[0]: (math.log((count_total - t[1] + 0.5) / t[1] + 0.5))
            for t in counts if t[1] != 0}
    print idfs

BM25('Existing methods for ranking aggregation includes unsupervised learning methods such as BordaCount and Markov Chain, and supervised learning methods such as Cranking.', 'Markov Chain based ranking aggregation assumes that there exists a Markov Chain on the' +
     'objects. The basic rankings of objects are utilized to construct the Markov Chain, in the way thatthe transition probabilities are estimated based on the order relations in the rankings.',
     'tac')
