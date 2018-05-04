# encoding: utf-8

'''

@author: ZiqiLiu


@file: relationship.py

@time: 2018/4/16 下午11:23

@desc:
'''
import numpy as np
from module import Entity2, Token
from collections import deque, defaultdict
import re
import pickle
import json
from module import MyMention, MyNER
from functools import reduce


class RelationshipGolden(object):
    PERSON = 1

    def __init__(self, charList, id=-1, pipeline=None, text='', threshold=25,
                 verbose=True):
        pat = re.compile(r'\n+')
        self.id = id
        self.verbose = verbose
        self.threshold = threshold
        self.pipeline = pipeline
        self.entityMap = {}
        self.text = pat.sub(' ', text)

        i = 0
        self.char2id = {}
        self.id2char = defaultdict(list)
        self.family = set()
        self.family2char = defaultdict(list)
        self.char2family = {}
        single_character = charList['null']
        for char in single_character:
            words = char.split()
            for w in words:
                self.char2id[w] = i
            self.id2char[i] = words
            i += 1
        del charList['null']
        for family in charList:
            self.family.add(family)
            for char in charList[family]:
                words = char.split()
                for w in words:
                    self.char2id[w] = i
                    self.family2char[family].append(i)
                self.id2char[i] = words
                self.char2family[i] = family
                i += 1
        print(self.family)
        print(self.char2id)
        print(self.id2char)

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
        return
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

    def _happenRelationship(self, e1: Entity2, e2: Entity2):
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

        doc_text = [d.text.strip().lower() for d in doc]  # list of tokens

        filtered_ner = self._NERfilter(doc.ents)

        ner = np.zeros((len(doc)), dtype=np.int32)

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
                name = ' '.join(doc_text[st:end])
                if name == '':
                    raise Exception('fuck')

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

            # no valid entity name
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
        :return: ent (could be None) if only family name appear, 
        then return family entity
        '''
        ent = None

        uniqNames, flag, minus_count = self._coref_names_filter(names)

        if not flag:
            if self.verbose:
                print('wrong coref chain', names)
            return ent
        existing_ents = set()
        for n in uniqNames:
            if n in self.char2id:
                if self.char2id[n] in self.entityMap:
                    existing_ents.add(self.entityMap[self.char2id[n]])
            elif n in self.family:
                if n in self.entityMap:
                    existing_ents.add(self.entityMap[n])
            else:
                raise Exception('sth wrong here')

        if len(existing_ents) >= 2:
            print(existing_ents)
            print(uniqNames)
            raise Exception('sth wrong here')

        if len(existing_ents) == 1:
            ent = list(existing_ents)[0]
        else:
            # create new one

            isChar = True if uniqNames[0] in self.char2id else False
            print('create new', uniqNames, isChar)
            key = self.char2id[uniqNames[0]] if isChar else uniqNames[0]
            ent = Entity2(id=key, family=not isChar)
            self.entityMap[key] = ent
        ent.names.update(uniqNames)
        # if not self.check(ent.names):
        #     print(uniqNames)
        #     print(ent.names)
        #     raise Exception('fuckoff')
        ent.freq += count - minus_count
        return ent

    # def check(self, names):
    #     names = list(names)
    #     if names[0] in self.char2id:
    #         if any(n in self.family for n in names):
    #             return False
    #         if len(set(self.char2id[n] for n in names)) > 1:
    #             return False
    #     else:
    #         if any(n in self.char2id for n in names):
    #             return False
    #         if len(names) > 1:
    #             return False
    #     return True

    def _coref_names_filter(self, names, threshold=0.8, debug=False):
        '''
        
        :param names: names from coref chain
        :return: uniqNames : list of str, flag: bool
        '''
        flatten_names = reduce(lambda a, b: a + b,
                               [name.split() for name in names])
        family = set()
        char = set()
        charDict = defaultdict(int)
        for n in flatten_names:
            if n in self.family:
                family.add(n)
            elif n in self.char2id:
                charDict[self.char2id[n]] += 1
                char.add(n)
            else:
                print(names)
                print(n)
                print(flatten_names)
                raise Exception('sth wrong here')

        if len(family) > 1:
            print('more than one family!', family)
            return [], False, 0
        if len(charDict) == 0:
            # only family name appear
            if len(family) == 0:
                print(names)
                print(flatten_names)
                raise Exception('sth wrong here')
            return list(family), True, 0
        elif len(charDict) == 1:
            return list(char), True, 0
        else:
            # more than one entity in this chain
            freqTuple = sorted(charDict.items(), key=lambda x: -x[1])
            total = sum(charDict.values())
            if freqTuple[0][1] / total > threshold:

                return [n for n in char if
                        n in self.id2char[freqTuple[0][0]]], True, \
                       total - freqTuple[0][1]
            else:
                return [], False, 0

    def _getEntity_NER(self, start_idx, end_idx, doc_text, tokens):
        names = doc_text[start_idx:end_idx]
        char_name = []
        family_name = set()
        isChar = False
        charIDs = set()
        ent_char = None
        ent_family = None
        for n in names:
            if n in self.char2id:
                char_name.append(n)
                charIDs.add(self.char2id[n])
                if self.char2id[n] in self.entityMap:
                    ent_char = self.entityMap[self.char2id[n]]
            if n in self.family:
                family_name.add(n)
                if n in self.entityMap:
                    ent_family = self.entityMap[n]
        if len(charIDs) > 1 or len(family_name) > 1:
            return
        if ent_char:
            ent = ent_char
            isChar = True
        elif ent_family:
            ent = ent_family
        else:
            # create new one
            isChar = len(char_name) > 0
            key = self.char2id[names[0]] if isChar else names[0]
            ent = Entity2(id=key, family=not isChar)
            self.entityMap[key] = ent

        ent.freq += 1
        ent.names.update(char_name if isChar else family_name)
        # if not self.check(ent.names):
        #     print(ent.names)
        #     raise Exception('fuck111')

        tokens.append(Token(absPos=start_idx, name=' '.join(names), entity=ent))

    def _getSpan(self, arr):
        '''
        
        :param arr: list of 0 and 1
        :return: 
        '''
        span = []
        start_ind = None
        flag = False
        for i, w in enumerate(arr):
            if w:
                if not flag:
                    start_ind = i
                    flag = True
                if i == len(arr) - 1:
                    span.append((start_ind, i + 1))
            else:
                if flag:
                    span.append((start_ind, i))
                    flag = False
        return span

    def _NERfilter(self, ners: list):
        '''
        cut ners, keep Upper case word only
        :param ners: 
        :return: list of MyNer
        '''
        res = []
        for e in ners:
            arr = [1 if self.validEntity(e.doc[i].text.strip().lower()) else 0
                   for i in range(e.start, e.end)]
            span = self._getSpan(arr)

            for start, end in span:
                res.append(
                    MyNER(e.doc[start:end].text.lower(), e.start + start,
                          e.start + end))

        return res

    def validEntity(self, word):
        return word in self.char2id or word in self.family

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
        print(self)
