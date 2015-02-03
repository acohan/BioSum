'''
Created on Jan 11, 2015

@author: rmn
'''
from util.documents_model import DocumentsModel
from collections import defaultdict
import json
import codecs
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
from copy import deepcopy

doc_mod = DocumentsModel('../data/TAC_2014_BiomedSumm_Training_Data')
with codecs.open('../data/v1-2a.json', 'rb', 'utf-8') as mf:
    data = json.load(mf)

docs = doc_mod.get_all()
docs_new = {}

'''
return a list which is the union of a list of offsets s
e.g. [[1,10],[5,15]] -> [[1,15]]
'''


def union(s):
    s.sort(key=lambda x: x[0])
    y = [s[0]]
    for x in s[1:]:
        if y[-1][1] < x[0]:
            y.append(x)
        elif y[-1][1] >= x[0]:
            y[-1][1] = max(x[1], y[-1][1])
    return y


def sent_tokenize(data, filter_threshold=None):
    '''
    Tokenizes a string into sentences and corresponding offsets

    Args:
        data(str): The document itself 
        filter_threshold(int): if sentence length is
            less than this, it will be ignored

    Returns:
        tuple(list(str), list(list))): tokenized
            sentences and corresponding offsets
    '''
    punkt_param = PunktParameters()
    punkt_param.abbrev_types = set(
        ['dr', 'vs', 'mr', 'mrs', 'prof', 'inc', 'et', 'al', 'Fig', 'fig'])
    sent_detector = PunktSentenceTokenizer(punkt_param)
    sentences = sent_detector.tokenize(data)
    offsets = sent_detector.span_tokenize(data)
    return (sentences, offsets)


def get_data():
    for tid, did in docs.iteritems():
        if tid not in docs_new:
            docs_new[tid] = {}
        for _, ann in data[tid.upper()].iteritems():
            for annotation in ann:
                cit = annotation['citance_number']
                if cit not in docs_new[tid]:
                    docs_new[tid][cit] = {}
                if 'ref_offset' not in docs_new[tid][cit]:
                    docs_new[tid][cit]['ref_offset'] =\
                        annotation['reference_offset']
                else:
                    docs_new[tid][cit]['ref_offset'] = union(
                        docs_new[tid][cit]['ref_offset'] + annotation['reference_offset'])

                if 'cit_offset' not in docs_new[tid][cit]:
                    docs_new[tid][cit]['cit_offset'] =\
                        [annotation['citation_offset']]
                else:
                    docs_new[tid][cit]['cit_offset'] = union(
                        docs_new[tid][cit]['cit_offset'] + [annotation['citation_offset']])

                docs_new[tid][cit]['ref_art'] = annotation['reference_article']
                docs_new[tid][cit]['cit_art'] = annotation['citing_article']

    for tid in docs_new:
        for cit in docs_new[tid]:
            docs_new[tid][cit]['ref_text'] =\
                [(s, doc_mod.get_doc(tid,
                                     docs_new[tid][cit]['ref_art'].lower(),
                                     interval=s)) for s in
                 docs_new[tid][cit]['ref_offset']]
            docs_new[tid][cit]['cit_text'] =\
                [(s, doc_mod.get_doc(tid,
                                     docs_new[tid][cit]['cit_art'].lower(),
                                     interval=s)) for s in
                 docs_new[tid][cit]['cit_offset']]
            docs_new[tid][cit]['not_relevant'] = doc_mod.get_doc(
                tid, docs_new[tid][cit]['cit_art'].lower())
#             docs_new[tid][cit]['relevant'] = 

#     print docs_new.keys()
#     print docs_new['D1418_TRAIN'.lower()]
#     return docs_new

get_data()
print docs_new.values()[0].values()[0]['cit_text']
