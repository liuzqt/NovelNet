# encoding: utf-8

'''

@author: ZiqiLiu


@file: main.py

@time: 2018/4/13 下午5:19

@desc:
'''

from relationship import Relationship
from neuralcoref import Coref
from glob import glob

def process_text(path='Harry_Potter_and_the_Sorcerers_Stone.txt'):

    coref = Coref()

    text = "Stan Smith study in Pittsburgh, and he has a beautiful daughter called Annie. Smith is a teacher of Alex. Alex is a good boy and he is handsome. Bobby is a dog. The driver is stupid."

    with open("Harry_Potter_and_the_Sorcerers_Stone.txt", 'r') as f:
        text = f.read()

    relationship = Relationship(0, pipeline=coref, text=text, threshold=20,
                                debug=True)
    relationship.build_relationship()
    relationship.report()
    relationship.export_graph()

def process_pkl():
    coref = Coref()


if __name__ == '__main__':
    process_pkl()