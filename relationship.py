# encoding: utf-8

'''

@author: ZiqiLiu


@file: relationship.py

@time: 2018/4/16 下午11:23

@desc:
'''
import numpy as np
from module import Entity, Token
from collections import deque, Counter
import re
from word_similarity import isSimilar
import pickle
import json
from module import MyMention, MyNER


class Relationship(object):
    pronoun = {"he", "she", "it", "him", "her", "they", "them", "this", "that"}
    PERSON = 1

    def __init__(self, id=-1, pipeline=None, text='', threshold=25,
                 verbose=True):
        pat = re.compile(r'\n+')
        self.id = id
        self.ner = set()
        self.mergeCount = 0
        self.verbose = verbose
        self.entityCount = 0
        self.threshold = threshold
        self.pipeline = pipeline
        self.entityMap = {}
        self.text = pat.sub(' ', text)
        self.removed = set()

    def build_relationship(self):
        tokens = self.parseCoref(self.text)
        self.parseRelationship(tokens)

    def build_relationship_from_pkl(self, doc_pkls, clusters_pkls,
                                    mentions_pkls):
        assert len(doc_pkls) == len(clusters_pkls) == len(mentions_pkls)
        print('total %d files to process' % len(doc_pkls))
        for doc, clusters, mentions in zip(doc_pkls, clusters_pkls,
                                           mentions_pkls):
            print('processing %s,%s,%s...' % (doc, clusters, mentions))
            with open(doc, 'rb') as f:
                _doc = pickle.load(f)
            with open(clusters, 'rb') as f:
                _clusters = pickle.load(f)
            with open(mentions, 'rb') as f:
                _mentions = pickle.load(f)
            tokens = self.parseCoref(None, _doc, _clusters, _mentions)
            self.parseRelationship(tokens)

    def export_graph(self):
        '''
        
        :return: 
        '''
        ents = dict((ent, str(idx)) for idx, ent in
                    enumerate(set(self.entityMap.values())))
        output = []
        nbs = set()
        for e in ents:
            nbs.update(e.neighbors.keys())
        assert len(ents) >= len(nbs)

        for ent, i in ents.items():
            temp = {'id': i,
                    'freq': ent.freq,
                    'names': list(ent.names),
                    'neighbor': dict((ents[nb], weight)
                                     for nb, weight in ent.neighbors.items())}
            output.append(temp)
        if self.verbose:
            print(output)
        with open('./graph.json', 'w') as f:
            json.dump(output, f)
        print('graph dumped to json.')

    def parseRelationship(self, tokens):
        # Noticed that the tokens are sorted in their text order
        queue = deque()
        for token in tokens:
            while len(queue) > 0 \
                    and token.absPos - queue[0].absPos > self.threshold:
                queue.popleft()
            for nb in queue:
                self._happenRelationship(token.entity, nb.entity)
            queue.append(token)

    def _happenRelationship(self, e1: Entity, e2: Entity):
        '''
        
        :param e1: Entity 
        :param e2: Entity
        :return: 
        '''
        if e1 != e2:
            e1.neighbors[e2] = e1.neighbors.get(e2, 0) + 1
            e2.neighbors[e1] = e2.neighbors.get(e1, 0) + 1

    def parseCoref(self, text, doc=None, clusters=None, mentions=None):
        tokens = []

        if text:
            self.pipeline.continuous_coref(utterances=text)
            doc = self.pipeline.get_utterances()[0]

            # clusters id is corresponding to mentions
            clusters = self.pipeline.get_clusters(remove_singletons=True)[
                0]  # ({1: [1], [1]}
            mentions = [MyMention(m) for m in self.pipeline.get_mentions()]

            doc_name = 'doc' + str(self.id) + '.pkl'
            clusters_name = 'clusters' + str(self.id) + '.pkl'
            mentions_name = 'mentions' + str(self.id) + '.pkl'

            with open(doc_name, 'wb') as f:
                pickle.dump(doc, f)
            with open(clusters_name, 'wb') as f:
                pickle.dump(clusters, f)
            with open(mentions_name, 'wb') as f:
                pickle.dump(mentions, f)

        doc_text = [d.text.strip() for d in doc]  # list of tokens

        filtered_ner = self._NERfilter(doc.ents)

        ner = np.zeros((len(doc)), dtype=np.int32)
        self.ner.update([str(e) for e in filtered_ner])
        for ent in filtered_ner:
            ner[ent.start:ent.end] = 1

        # this is useful when parsing NER, to avoid duplicate entry from Coref,
        # identified as absPos
        token_map = {}

        if self.verbose:
            print('%d chain detected.' % len(clusters))
            name_clusters = [
                [(mentions[idx].text, mentions[idx].start) for idx in cluster]
                for cluster
                in clusters.values()]

            for cluster in name_clusters:
                print(cluster)

        def name_filter(m):
            '''
            check how many entity in this mention token, and cut the name
            
            :param m: Mention Token
            :return: a tuple of (m, modify_name, absPos, display_name)
            '''

            ents_span = []
            pre = False
            start_idx = -1
            name = None
            for j in range(m.start, m.end):
                if ner[j] == self.PERSON:
                    if not pre:
                        start_idx = j
                        pre = True
                    if j == m.end - 1:
                        ents_span.append((start_idx, j + 1))
                else:
                    if pre:
                        pre = False
                        ents_span.append((start_idx, j))
            if len(ents_span) > 1:
                # more than one entity
                if self.verbose:
                    print('more than one entity in one coref mention!', m.text)
            elif len(ents_span) == 1:
                st, end = ents_span[0]
                name = ' '.join(doc_text[st:end]).lower()

            display_name = name if name is not None else m.text
            return m, name, ents_span[0][0] if len(
                ents_span) > 0 else m.start, display_name

        # parse Coref
        if self.verbose:
            print('\n\nparsing coref.....\n')
        for wtf, chain in clusters.items():
            if self.verbose:
                print(wtf)
            # chain is only id for mention tokens
            ms = [mentions[idx] for idx in chain]

            ms_tuple = [name_filter(m) for m in ms]
            names = list(
                filter(lambda x: x is not None, (x[1] for x in ms_tuple)))

            # if all entity names don't contains uppercase char
            if len(names) == 0:
                if self.verbose:
                    print('empty chain, skip', ms)
                continue

            if self.verbose:
                print(names, ms)

            ent = self._getEntity_coref(names=names, count=len(ms))
            if not ent:
                continue
            for m, modified_name, absPos, display_name in ms_tuple:
                token = Token(absPos, display_name, ent)
                tokens.append(token)
                token_map[absPos] = token

        # important!
        # some tokens' entity might be removed during the merge process
        # so we need to substitute it
        for tk in tokens:
            if tk.entity in self.removed:
                tk.entity = self.entityMap[next(iter(tk.entity.names))]
        temp = set(self.entityMap.values())

        # parse NER

        start_idx = -1
        pre = False
        for i in range(len(ner)):
            if ner[i] == self.PERSON:
                if not pre:
                    pre = True
                    start_idx = i
                if i == len(ner) - 1:
                    # end of array
                    if start_idx not in token_map:
                        self._getEntity_NER(start_idx=start_idx, end_idx=i + 1,
                                            doc_text=doc_text, tokens=tokens)
            else:
                if pre:
                    pre = False
                    if start_idx not in token_map:
                        self._getEntity_NER(start_idx=start_idx, end_idx=i,
                                            doc_text=doc_text, tokens=tokens)

        tokens.sort(key=lambda x: x.absPos)

        if self.verbose:
            print("\n\ntokens sorted in text order:")
            for tk in tokens:
                print("%s\t%d" % (tk.name, tk.absPos))
        return tokens

    def _getEntity_coref(self, names: list, count: int):
        '''
        
        :param names: list of str. entity names (filtered, Upper char only)
        :param count: occurrence count, used for update entity freq
        :return: ent (could be None)
        '''
        removed = None
        ent = None
        # calculate word similarity to determine whether there're more than
        # one entity
        uniqNames, flag = self._coref_names_filter(names)

        if not flag:
            if self.verbose:
                print('wrong coref chain', names)
            return ent

        existing_ents = list(set(self.entityMap[name] for name in uniqNames if
                                 name in self.entityMap))

        if len(existing_ents) == 1:
            ent = existing_ents[0]
        elif len(existing_ents) > 1:
            # hopefully we won't meet this case
            print()
            print('merge!!!', [e.names for e in existing_ents])
            print('uniqNames', uniqNames)
            # self._coref_names_filter(names, debug=True) # for debug purpose

            removed = []
            # merge entities
            self.mergeCount += len(existing_ents) - 1
            merge = existing_ents[0]
            for to_merge in existing_ents[1:]:
                removed.append(to_merge)
                self.removed.add(to_merge)
                # merge freq
                merge.freq += to_merge.freq
                # merge names
                merge.names.update(to_merge.names)
                # merge neighbor
                for nb, ct in to_merge.neighbors.items():
                    if nb in existing_ents:
                        nb.neighbors.pop(to_merge)
                    else:
                        merge.neighbors[nb] = merge.neighbors.get(nb, 0) + ct
                        nb.neighbors[merge] = nb.neighbors.get(merge, 0) + ct
                        nb.neighbors.pop(to_merge)

            ent = merge
        else:
            # create new one
            self.entityCount += 1
            ent = Entity(self.entityCount)

        ent.names.update(uniqNames)
        ent.freq += count
        for name in ent.names:
            self.entityMap[name] = ent
        return ent

    def _coref_names_filter(self, names, threshold=0.8, debug=False):
        '''
        
        :param names: names from coref chain
        :return: uniqNames,flag
        '''
        # current implementation it to do longest-common-substring match pair-wise
        nameDict = Counter(names)
        uniqNames = list(nameDict.keys())
        total = len(names)
        mat = np.tile(np.array([nameDict[k] for k in uniqNames]),
                      (len(uniqNames), 1))
        for i in range(len(uniqNames) - 1):
            for j in range(i + 1, len(uniqNames)):
                if not isSimilar(uniqNames[i], uniqNames[i + 1]):
                    mat[i][j] = mat[j][i] = 0

        remain_inds = [i for i, row in enumerate(mat) if
                       row.sum() / total >= threshold]
        if len(remain_inds) == 0:
            return [], False
        remain_mat = mat[remain_inds, :][:, remain_inds]
        if debug:
            print('debug')
            print(mat)
            print(uniqNames)
            print(remain_mat)
        if (remain_mat == 0).sum() > 0:
            if self.verbose:
                print('flag2', nameDict)
            return uniqNames, False
        new_names = [uniqNames[i] for i in remain_inds]
        return new_names, True

    def _getEntity_NER(self, start_idx, end_idx, doc_text, tokens):
        name = ' '.join(doc_text[start_idx:end_idx]).lower()
        if name in self.entityMap:
            ent = self.entityMap[name]
        else:
            self.entityCount += 1
            ent = Entity(self.entityCount)

        ent.freq += 1
        ent.names.add(name)
        self.entityMap[name] = ent
        tokens.append(Token(absPos=start_idx, name=name, entity=ent))

    def _NERfilter(self, ners: list):
        '''
        cut ners, keep Upper case word only
        :param ners: 
        :return: 
        '''
        res = []
        for e in ners:
            start_ind = -1
            for i in range(e.start, e.end):
                if e.doc[i][0].isupper():
                    start_ind = i
                    break
            if start_ind == -1:
                continue
            end_ind = -1
            for i in range(e.end - 1, e.start - 1, -1):
                if e.doc[i][0].isupper():
                    end_ind = i + 1
                    break
            res.append(
                MyNER((e.doc[start_ind:end_ind]).text, start_ind, end_ind))

        return res

    @property
    def totalEntityNum(self):
        return self.entityCount - self.mergeCount

    def __str__(self):

        sortedEntity = sorted(set(self.entityMap.values()),
                              key=lambda x: x.freq,
                              reverse=True)
        report = 'Total %d entities.\n\n' % len(sortedEntity)
        report += "Entities sorted by frequency:\n"
        for ent in sortedEntity:
            report += "%s\t%d\n" % (ent, ent.freq)

        report += '\n\nRelationship\n'
        for ent in sortedEntity:
            report += '=' * 30 + '\n'
            report += str(ent) + '\n'
            report += '-' * 20 + '\n'
            for nb, ct in ent.neighbors.items():
                report += '%s\t%d\n' % (nb, ct)
        return report

    def report(self):
        with open('./ner' + str(self.id) + '.txt', 'w') as f:
            for ner in self.ner:
                f.write(ner + '\n')
        print(self)
        names = set()
        for e in set(self.entityMap.values()):
            for name in e.names:
                if name in names:
                    print('duplicate name', name)
                names.add(name)
