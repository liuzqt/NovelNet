# encoding: utf-8

'''

@author: David


@file: sentiment.py.py

@time: 14:36 

@desc:
'''

import pickle
from nltk.sentiment.vader import SentimentIntensityAnalyzer

def data_prepare(file):
    relationships = {}
    with open(file, 'rb') as f:
        sentences = pickle.load(f)
    for sentence in sentences:
        if len(sentence[1]) > 4:
            continue
        rname = ""
        names = sorted(sentence[2])
        for name in names:
            rname += (",".join(name)) + "+"

        rname = rname.rstrip("+")
        if rname not in relationships:
            relationships[rname] = []
        relationships[rname].append(sentence[0])
    return relationships



def sentiment_score(relationships):
    sid = SentimentIntensityAnalyzer()
    result = {}

    for r in relationships:
        p = n = c = 0
        for sentence in relationships[r]:
            # print(sentence)
            ss = sid.polarity_scores(sentence)
            p += ss['pos']
            n += ss['neg']
            c += ss['compound']
        rl = r.split("+")
        for j in range(len(rl)):
            for k in range(j + 1, len(rl)):
                if str(rl[j] + "+" + rl[k]) not in result:
                    result[str(rl[j] + "+" + rl[k])] = 0.0
                result[str(rl[j] + "+" + rl[k])] += c
    out = sorted(result.items())
    return out

def main():
    out = sentiment_score(data_prepare("relationshipSentence.pkl"))
    with open("sentiment", "w") as f:
        for i in out:
            f.write(i[0] + ":" + str(i[1]))
            f.write("\n")
