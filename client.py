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
        print("try job" + j)
        flag = 0
        while flag == 0:
            for m in machine_list:
                if check_machine(m):
                    print(m + " is idle")
                    if assign(m, j):
                        print("assign " + j +" to " + m)
                        flag = 1
                        break
            if flag == 0:
                print("all are busy, wait 1 minutes")
                time.sleep(60)
        time.sleep(1)
    return True
def check_machine(machine):
    r = requests.get(machine)
    if r.status_code != 200:
        return False
    print(r.content)
    if r.content == b"The server is idle":
        return True
    else:
        return False

def assign(machine, job):
    r = requests.get(machine,{'name':job})
    if r.status_code != 200:
        return False
    if r.content.decode("utf-8").startswith("start"):
        return True
    return False

def main():
    jobs = ['hp1_0', 'hp1_1', 'hp1_2', 'hp1_3', 'hp1_4', 'hp1_5', 'hp1_6', 'hp1_7', 'hp1_8',
            'hp1_9', 'hp1_10', 'hp1_11', 'hp1_12', 'hp1_13', 'hp1_14', 'hp1_15', 'hp1_16', 'hp1_17']
    #jobs = ['test1','test2','test3','test4','testtext']
    machines = ["http://35.229.88.233:5000/job", "http://35.190.137.170:5000/job", "http://35.196.226.39:5000/job"]
    runjob(jobs, machines)

if __name__ == '__main__':
    main()
