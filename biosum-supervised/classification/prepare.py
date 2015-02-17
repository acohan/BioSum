'''
Created on Feb 12, 2015

@author: rmn
'''

from util.es_interface import ESInterface


class Prep(object):

    def __init__(self, index='biosum'):
        self.es_int = ESInterface(index_name=index)

    def prep_data(self, doc_type, relevant_offsets):
        '''
        Prepares the training data for leaning to rank
        '''
        hits = self.es_int.find_all(doc_type=doc_type)
        x_train = []
        y_train = []
        for hit in hits:
            label = 0
            offset = eval(hit['_source']['offset'])
            for off in relevant_offsets:
                if self.get_overlap(offset, off) > 0:
                    label = 1
                    break
            x_train.append(hit['_source']['sentence'])
            y_train.append(label)

        print x_train[0:3]
        print y_train[0:3]

    def get_overlap(self, a, b):
        return max(0, min(a[1], b[1]) - max(a[0], b[0]))

if __name__ == '__main__':
    p = Prep()
    p.prep_data("d1409_train_sherr", [[200, 500], [1000, 1200]])
