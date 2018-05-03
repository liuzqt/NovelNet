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
                    assign(m, j)
                    flag = 1
                    break
            time.sleep(60)

def check_machine(machine):
    return True

def assign(machine, job):
    pass

def main():
    pass
