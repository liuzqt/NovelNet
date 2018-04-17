# encoding: utf-8

'''

@author: ZiqiLiu


@file: relationship.py

@time: 2018/4/16 下午11:23

@desc:
'''
import numpy as np
from module import Entity, Token
from collections import deque
import re


class Relationship(object):
    pronoun = ["he", "she", "it", "him", "her", "they", "them", "this", "that"]
    PERSON = 1

    def __init__(self, pipeline, text, threshold=25, debug=True):
        pat = re.compile(r'\n+')
        self.ner = set()
        self.mergeCount = 0
        self.debug = debug
        self.entityCount = 0
        self.threshold = threshold
        self.pipeline = pipeline
        self.entityMap = {}
        # self.entitySet = set()
        text = pat.sub(' ', text)

        tokens = self.parseCoref(text)
        self.parseRelationship(tokens)

    def parseRelationship(self, tokens):
        # Noticed that the tokens are sorted in their text order
        queue = deque()
        for m in tokens:
            while len(queue) > 0 and m.absPos - queue[
                0].absPos > self.threshold:
                queue.popleft()
            for nb in set(queue):
                self._happenRelationship(m.entity, nb.entity)
            queue.append(m)

    def _happenRelationship(self, e1, e2):
        '''
        
        :param e1: Entity 
        :param e2: Entity
        :return: 
        '''
        if e1 != e2:
            e1.neighbors[e2] = e1.neighbors.get(e2, 0) + 1
            e2.neighbors[e1] = e2.neighbors.get(e1, 0) + 1

    def parseCoref(self, text):
        tokens = []

        self.pipeline.continuous_coref(utterances=text)
        doc = self.pipeline.get_utterances()[0]
        doc_text = [d.text.strip() for d in doc]

        filtered_ner = list(
            filter(lambda x: self._NERfilter(x), doc.ents))
        ner = np.zeros((len(doc)), dtype=np.int32)
        self.ner.update([str(e) for e in filtered_ner])
        for ent in filtered_ner:
            ner[ent.start:ent.end] = 1

        # clusters id is corresponded to mentions
        clusters = self.pipeline.get_clusters(remove_singletons=True)[
            0]  # ({1: [1], [1]}
        mentions = self.pipeline.get_mentions()
        # this is useful when parsing NER, to avoid duplicate entry from Coref, identified as absPos
        token_map = {}

        if self.debug:
            print('%d chain detected.' % len(clusters))
            name_clusters = [
                [(mentions[idx].text, mentions[idx].start) for idx in cluster]
                for cluster
                in clusters.values()]

            for cluster in name_clusters:
                print(cluster)

        def name_filter(m):
            '''
            check how many entity in this mention token, and cut the name to entity name
            :param m: 
            :return: a tuple of (m, modify_name, absPos,display_name)
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
                print('fuck!')
                print(m.text)
            elif len(ents_span) == 1:
                st, end = ents_span[0]
                name = ' '.join(doc_text[st:end]).lower()
            display_name = name if name is not None else m.text
            return m, name, ents_span[0][0] if len(
                ents_span) > 0 else m.start, display_name

        # parse Coref
        if self.debug:
            print('\n\nparsing coref.....\n')
        for _, chain in clusters.items():
            # chain is only id for mention tokens
            ms = [mentions[key] for key in chain]

            ms_tuple = [name_filter(m) for m in ms]
            names = list(
                filter(lambda x: x is not None, map(lambda x: x[1], ms_tuple)))
            if len(names) == 0:
                if self.debug:
                    print('empty chain, skip', ms)
                continue
            if self.debug:
                print(names, ms)
            ent = self._getEntity_coref(names=names, count=len(ms))

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
        if self.debug:
            print("\n\ntokens sorted in text order:")
            for tk in tokens:
                print("%s\t%d" % (tk.name, tk.absPos))
        return tokens

    def _getEntity_coref(self, names, count):

        ent = None

        existing_ents = [self.entityMap[name] for name in names if
                         name in self.entityMap]

        if len(existing_ents) == 1:
            ent = existing_ents[0]
        elif len(existing_ents) > 1:
            # hopefully we won't meet this case
            print('merge!!!', [e.names for e in existing_ents])
            # merge entities
            self.mergeCount += len(existing_ents) - 1
            merge = existing_ents[0]
            for to_merge in existing_ents[1:]:
                # remove from entitySet
                # self.entitySet.remove(to_merge)
                # merge freq
                merge.freq += to_merge.freq
                # merge names
                merge.names.update(to_merge.names)
                # merge neighbor
                for nb, ct in to_merge.neighbors.items():
                    if nb != merge:
                        merge.neighbors[nb] = merge.neighbors.get(nb, 0) + ct
                        nb.neighbors[merge] = nb.neighbors.get(merge, 0) + ct
                        nb.neighbors.pop(to_merge)
                    else:
                        merge.neighbors.pop(to_merge)
            ent = merge
        else:
            # create new one
            self.entityCount += 1
            ent = Entity(self.entityCount)

        # self.entitySet.add(ent)
        ent.names.update(names)
        ent.freq += count
        for name in ent.names:
            self.entityMap[name] = ent
        return ent

    def _getEntity_NER(self, start_idx, end_idx, doc_text, tokens):
        name = ' '.join(doc_text[start_idx:end_idx]).lower()
        if name in self.entityMap:
            ent = self.entityMap[name]
        else:
            self.entityCount += 1
            ent = Entity(self.entityCount)

        ent.freq += 1
        ent.names.add(name)
        # self.entitySet.add(ent)
        self.entityMap[name] = ent
        tokens.append(Token(absPos=start_idx, name=name, entity=ent))

    def _NERfilter(self, e):
        words = e.text.split()
        return any(w[0].isupper() for w in e.text.split())

    @property
    def totalEntityNum(self):
        return self.entityCount - self.mergeCount

    def __str__(self):
        report = ''
        sortedEntity = sorted(set(self.entityMap.values()),
                              key=lambda x: x.freq,
                              reverse=True)
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
        with open('./ner.txt', 'w') as f:
            for ner in self.ner:
                f.write(ner + '\n')
        print(self)
        print(self.ner)
