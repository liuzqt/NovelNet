# encoding: utf-8

'''

@author: David


@file: server.py

@time: 20:31 

@desc:
'''

from flask import Flask
from flask import request
import boto3
import io
from relationship import Relationship
from neuralcoref import Coref
from concurrent.futures import ThreadPoolExecutor
import os


executor = ThreadPoolExecutor(2)
app = Flask(__name__)

@app.route('/')
def heartbeat():
    return "I am alive"



@app.route('/job')
def runjob():
    if os.path.exists('./status'):
        with open('status', 'r') as f:
            id = f.read()
        return "this server is running file " + id
    filename = request.args.get('name', '')
    if filename == '':
        return "The server is idle"
    print(filename)
    with open('status', 'w') as f:
        f.write(filename)
    executor.submit(rnn, filename)
    return "start running" + filename




def rnn(filename):
    bucket_name = "novelnet"
    coref = Coref()
    print("job " + filename + " is started")
    s3 = boto3.resource('s3')
    s3.Object("novelnet", filename).download_file("test")
    with open("test", 'r') as f:
        text = f.read()
    #print(text)
    relationship = Relationship(id=filename, pipeline=coref, text=text, threshold=20, debug=False)
    relationship.report()
    doc_name = 'doc' + filename + '.pkl'
    clusters_name = 'clusters' + filename + '.pkl'
    mentions_name = 'mentions' + filename + '.pkl'
    ner_name = 'ner' + filename + '.txt'
    s3.Object(bucket_name, "results/" + doc_name).upload_file(doc_name)
    s3.Object(bucket_name, "results/" + clusters_name).upload_file(clusters_name)
    s3.Object(bucket_name, "results/" + mentions_name).upload_file(mentions_name)
    s3.Object(bucket_name, "results/" + ner_name).upload_file(ner_name)
    os.remove("status")
    os.remove("test")
    print("job " + filename + " is finished")


if __name__ == '__main__':
      app.run()
