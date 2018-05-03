# encoding: utf-8

'''

@author: David


@file: client.py

@time: 22:01 

@desc:
'''

import requests
import boto3
import time


def runjob(joblist, machine_list):
    print(joblist)
    for j in joblist:
        flag = 0
        while flag == 0:
            for m in machine_list:
                if check_machine(m):
                    if assign(m, j):
                        print("assign " + j +" to " + m)
                        flag = 1
                        break
            time.sleep(60)
    return True
def check_machine(machine):
    r = requests.get(machine)
    if r.content == "The server is idle":
        return True
    else:
        return False

def assign(machine, job):
    r = requests.get(machine,{'name':job})
    if r.content.startswith("start"):
        return True

def main():
    jobs = []
    machines = []
    runjob(jobs, machines)
