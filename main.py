# encoding: utf-8

'''

@author: ZiqiLiu


@file: main.py

@time: 2018/4/13 下午5:19

@desc:
'''

from relationship import Relationship
from relationship_golden import RelationshipGolden
from neuralcoref import Coref
from glob import glob
import json


def process_text(path='Harry_Potter_and_the_Sorcerers_Stone.txt'):
    coref = Coref()

    with open("Harry_Potter_and_the_Sorcerers_Stone.txt", 'r') as f:
        text = f.read()

    relationship = RelationshipGolden(0, pipeline=coref, text=text, threshold=25,
                                verbose=False)
    relationship.build_relationship()
    relationship.report()
    relationship.export_graph()


def process_pkl(path='./pkls/', n=None, charList=None):
    docs = sorted(glob(path + 'doc*'))
    mentions = sorted(glob(path + 'mention*'))
    clusters = sorted(glob(path + 'cluster*'))
    assert len(docs) == len(mentions) == len(clusters)

    relationship = RelationshipGolden(charList=charList, verbose=False)
    relationship.build_relationship_from_pkl(docs[:n], clusters[:n],
                                             mentions[:n])
    relationship.report()
    relationship.exportAll()


if __name__ == '__main__':
    with open('./charList.json', 'r') as f:
        charList = json.load(f)
    process_pkl(charList=charList)
