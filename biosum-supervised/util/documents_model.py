from __future__ import print_function
import os
import codecs
import charade
from util.tokenizer import para_tokenize
from collections import OrderedDict
from itertools import chain


def listfulldir(dir):
    return [os.path.join(dir, f) for f in os.listdir(dir)]


class DocumentsModel(object):

    def __init__(self, data_path, verbose=False):
        # data_path is the path to TAC_2014_BiomedSumm folder
        self.docs = {}
        self.verbose = verbose
        for topic_path in listfulldir(os.path.join(data_path, 'data')):
            topic = os.path.split(topic_path)[1].lower()
            self.docs.setdefault(topic, {})
            for doc_path in listfulldir(os.path.join(topic_path,
                                                     'Documents_Text')):
                doc = os.path.split(doc_path)[1][:-4].lower()

                with codecs.open(doc_path, mode='rb',
                                 encoding='utf-8', errors='strict') as df:
                    try:
                        self.docs[topic][doc] = df.read().replace('\r', '')
                    except UnicodeDecodeError:
                        with file(doc_path, mode='rb') as df:
                            frmt = charade.detect(df.read())['encoding']
                        with codecs.open(doc_path, mode='rb', encoding=frmt,
                                         errors='strict') as df:
                            self.docs[topic][doc] = df.read().replace('\r', '')
        if self.verbose:
            print('list of topics: %s' % '; '.join(self.docs.keys()))
            dnames = set(chain(*[d.keys() for d in self.docs.itervalues()]))
            print('list of doc_name: %s' % '; '.join(dnames))

        # create name aliases for incosistencies caused by ES
        for topic in self.docs.keys():
            for doc in self.docs[topic].keys():
                if doc.find(',') >= 0 or doc.find('\'') >= 0:
                    new_doc = doc.replace(',', '').replace('\'', '"')
                    self.docs[topic][new_doc] = self.docs[topic][doc]

        self.para_index = {}
        for topic in self.docs:
            self.para_index.setdefault(topic, {})
            for doc, data in self.docs[topic].iteritems():
                paragraphs = para_tokenize(self.docs[topic][doc])
                soff = [(s, e) for s, e in sorted(paragraphs['offsets'],
                                                  key=lambda x: x[0],
                                                  reverse=True)]
                self.para_index[topic][doc] = OrderedDict(soff)

    def get_para(self, topic_id, doc_name, interval):
        if self.verbose:
            print('request for "%s", "%s", "%s"' %
                  (topic_id, doc_name, interval))
        for s, e in self.para_index[topic_id][doc_name].iteritems():
            if interval[0] > s:
                return {'sentence': self.get_doc(topic_id, doc_name, (s, e)),
                        'offset': [s, e]}

    def get_doc(self, topic_id, doc_name, interval=None):
        '''
        Gets the document text
        Args:
            topic_id(str): id of the topic e.g. D1401_TRAIN
            doc_name(str): Document name e.g. chen.txt
            interval(tuple, optional): If specified, returns
                the text at a given interval offset

        Returns:
            unicode
        '''
        if self.verbose:
            print('request for "%s", "%s", "%s"' %
                  (topic_id, doc_name, interval))
        tid = topic_id.lower()
        did = doc_name.lower().replace('.txt', '')
        if interval:
            return self.docs[tid][did][interval[0]:interval[1]]
        else:
            return self.docs[tid][did]

    def get_doc_sentences(self, document, num, excetp_intervals):
        '''
        Returns a set of sentences from a document
        '''

    def get_doc_len(self, topic_id, doc_name):
        if self.verbose:
            print('request for "%s", "%s", "%s"' %
                  (topic_id, doc_name))
        tid = topic_id.lower()
        did = doc_name.lower().replace('.txt', '')
        self.docs[tid][did]

    def get_all(self):
        '''
        Returns:
            dict:
                keys: topic_id e.g. d1418_train
                    inner_keys:    document name e.g. 'yang,rosa'
        '''
        return self.docs
