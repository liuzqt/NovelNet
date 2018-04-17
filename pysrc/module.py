# encoding: utf-8

'''

@author: ZiqiLiu


@file: module.py

@time: 2018/4/16 下午11:14

@desc:
'''


class Entity(object):
    def __init__(self, id):
        self.id = id
        self.names = set()
        self.freq = 0
        self.neighbors = {}

    def __str__(self):
        return ','.join(self.names)


class Token(object):
    def __init__(self, absPos, name, entity):
        self.absPos = absPos
        self.name = name
        self.entity = entity

