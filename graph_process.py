# encoding: utf-8

'''

@author: David


@file: graph_process.py

@time: 12:14 

@desc:
'''


import json
import networkx as nx
import matplotlib.pyplot as plt


def transform(file):
    with open(file, 'r') as f:
        content = json.loads(f.read())
    names = []
    links = []
    id_mapping = {}
    freq_mapping = {}
    gr = nx.Graph()
    for c in content:
        if c['freq'] < 200:
            continue
        name = ",".join(c['names'])
        id_mapping[c['id']] = name
        names.append({"id": str(c['id']), "name": name, "value": c['freq']})
        freq_mapping[c['id']] = c['freq']
        gr.add_node(c['id'], label=name)
        gr.nodes[c['id']]['viz'] = {'size': int(c['freq'])}
    print(len(gr.nodes))
    for c in content:
        if c['id'] not in id_mapping:
            continue
        src = ",".join(c['names'])
        for t in c['neighbor']:
            if int(t) not in id_mapping:
                continue
            normalizer = max(c['freq'], freq_mapping[int(t)])

            if c['neighbor'][t] < 0.035 * normalizer:
                continue
            try:
                links.append({"source": str(c['id']), "weight": str(c['neighbor'][t]), "target": t})
                gr.add_edge(str(c['id']), t, weight=c['neighbor'][t])
            except:
                print(c['neighbor'][t])

    return gr, names,links



def main():
    gr, n,l = transform("graph.json")
    with open("names.json", 'w') as f:
        f.write(json.dumps(n))
    with open("links.json", 'w') as f:
        f.write(json.dumps(l))
    nx.write_gexf(gr, "test.gexf")



if __name__ == '__main__':
    main()
