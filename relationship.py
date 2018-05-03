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
import os


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
        if os.path.exists('./doc.pkl'):
            print('pkl file detected!')
            with open('doc.pkl', 'rb') as f:
                doc = pickle.load(f)
            with open('clusters.pkl', 'rb') as f:
                clusters = pickle.load(f)
            with open('mentions.pkl', 'rb') as f:
                mentions = pickle.load(f)
        else:
            self.pipeline.continuous_coref(utterances=text)
            doc = self.pipeline.get_utterances()[0]

            # clusters id is corresponding to mentions
            clusters = self.pipeline.get_clusters(remove_singletons=True)[
                0]  # ({1: [1], [1]}
            mentions = [MyMention(m) for m in self.pipeline.get_mentions()]

            with open('doc.pkl', 'wb') as f:
                pickle.dump(doc, f)
            with open('clusters.pkl', 'wb') as f:
                pickle.dump(clusters, f)
            with open('mentions.pkl', 'wb') as f:
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
            check how many entity in this mention token, and cut the name
            
            :param m: 
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
                print('more than one entity in one coref mention!', m.text)
            elif len(ents_span) == 1:
                st, end = ents_span[0]
                name = ' '.join(doc_text[st:end]).lower()
            display_name = name if name is not None else m.text
            return m, name, ents_span[0][0] if len(
                ents_span) > 0 else m.start, display_name

        # parse Coref
        if self.debug:
            print('\n\nparsing coref.....\n')
        for wtf, chain in clusters.items():
            print(wtf)
            # chain is only id for mention tokens
            ms = [mentions[idx] for idx in chain]

            ms_tuple = [name_filter(m) for m in ms]
            names = list(
                filter(lambda x: x is not None, (x[1] for x in ms_tuple)))

            # if all entity names don't contains uppercase char
            if len(names) == 0:
                if self.debug:
                    print('empty chain, skip', ms)
                continue

            if self.debug:
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
        if self.debug:
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

        ent = None
        # calculate word similarity to determine whether there're more than
        # one entity
        uniqNames, flag = self._coref_names_filter(names)

        if not flag:
            if self.debug:
                print('wrong coref chain', names)
            return ent

        existing_ents = [self.entityMap[name] for name in uniqNames if
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
        ent.names.update(uniqNames)
        ent.freq += count
        for name in ent.names:
            self.entityMap[name] = ent
        return ent

    def _coref_names_filter(self, names, threshold=0.8):
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
        remain_mat = mat[remain_inds, :][:, remain_inds]
        if (remain_mat == 0).sum() > 0:
            print('flag2', nameDict)
            return uniqNames, False
        new_names = [uniqNames[i] for i in remain_inds]
        print('flag4', new_names)
        if 'potter' in new_names:
            print('flag3')
            print(nameDict)
            print(remain_inds)
            print(new_names)
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
        # self.entitySet.add(ent)
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
            words = e.text.split()
            start_ind = 0
            for w in words:
                if w[0].isupper():
                    break
                else:
                    start_ind += 1
            if start_ind == len(words):
                continue
            end_ind = len(words)
            for w in words[::-1]:
                if w[0].isupper():
                    break
                else:
                    end_ind -= 1
            res.append(
                MyNER(' '.join(words[start_ind:end_ind]), e.start, e.end))

        return res

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
        names = set()
        for e in set(self.entityMap.values()):
            for name in e.names:
                if name in names:
                    print('duplicate name', name)
                names.add(name)

        print(len(self.entityMap), len(names))


class MyNER:
    def __init__(self, text, start, end):
        self.text = text
        self.start = start
        self.end = end

    def __str__(self):
        return self.text


class MyMention:
    def __init__(self, m):
        self.text = m.text
        self.start = m.start
        self.end = m.end

    def __str__(self):
        return self.text

    __repr__ = __str__