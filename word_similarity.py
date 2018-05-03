# encoding: utf-8

'''

@author: ZiqiLiu


@file: word_similarity.py

@time: 2018/4/27 下午4:11

@desc:
'''
import numpy as np


def isSimilar(word1: str, word2: str, threshold=.6):
    minlen = min(len(word1), len(word2))
    return lcs(word1, word2) / minlen >= threshold


def lcs(word1: str, word2: str):
    n, m = len(word1), len(word2)
    lcs_len = 0
    f = np.zeros((n + 1, m + 1))

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if word1[i - 1] == word2[j - 1]:
                f[i][j] = f[i - 1][j - 1] + 1
            else:
                f[i][j] = 0
            lcs_len = max(f[i][j], lcs_len)
    return lcs_len


if __name__ == '__main__':
    print(lcs('abcde', 'cgdegg'))
