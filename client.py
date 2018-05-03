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
    try:
        r = requests.get(machine)
    except:
        return False
    if r.status_code != 200:
        return False
    print(r.content)
    if r.content == b"The server is idle":
        return True
    else:
        return False

def assign(machine, job):
    try:
        r = requests.get(machine,{'name':job})
    except:
        return False
    if r.status_code != 200:
        return False
    if r.content.decode("utf-8").startswith("start"):
        return True
    return False

def main():
    jobs = ['hp2_4',
         'hp2_3',
         'hp2_2',
         'hp2_5',
         'hp2_9',
         'hp2_7',
         'hp2_6',
         'hp2_1',
         'hp2_8',
         'hp3_7',
         'hp3_18',
         'hp3_20',
         'hp3_16',
         'hp3_9',
         'hp3_11',
         'hp3_10',
         'hp3_8',
         'hp3_17',
         'hp3_21',
         'hp3_1',
         'hp3_19',
         'hp3_6',
         'hp3_3',
         'hp3_4',
         'hp3_12',
         'hp3_15',
         'hp3_14',
         'hp3_13',
         'hp3_5',
         'hp3_22',
         'hp3_2',
         'hp4_1',
         'hp4_6',
         'hp4_8',
         'hp4_9',
         'hp4_7',
         'hp4_13',
         'hp4_14',
         'hp4_22',
         'hp4_25',
         'hp4_24',
         'hp4_23',
         'hp4_15',
         'hp4_12',
         'hp4_30',
         'hp4_37',
         'hp4_36',
         'hp4_31',
         'hp4_5',
         'hp4_2',
         'hp4_3',
         'hp4_4',
         'hp4_28',
         'hp4_17',
         'hp4_10',
         'hp4_19',
         'hp4_26',
         'hp4_21',
         'hp4_20',
         'hp4_18',
         'hp4_27',
         'hp4_11',
         'hp4_29',
         'hp4_16',
         'hp4_34',
         'hp4_33',
         'hp4_32',
         'hp4_35',
         'hp5_24',
         'hp5_23',
         'hp5_15',
         'hp5_12',
         'hp5_13',
         'hp5_14',
         'hp5_22',
         'hp5_25',
         'hp5_2',
         'hp5_5',
         'hp5_4',
         'hp5_3',
         'hp5_38',
         'hp5_36',
         'hp5_31',
         'hp5_30',
         'hp5_37',
         'hp5_20',
         'hp5_18',
         'hp5_27',
         'hp5_11',
         'hp5_29',
         'hp5_16',
         'hp5_28',
         'hp5_17',
         'hp5_10',
         'hp5_19',
         'hp5_26',
         'hp5_21',
         'hp5_8',
         'hp5_6',
         'hp5_1',
         'hp5_7',
         'hp5_9',
         'hp5_32',
         'hp5_35',
         'hp5_34',
         'hp5_33',
         'hp6_2',
         'hp6_5',
         'hp6_4',
         'hp6_3',
         'hp6_20',
         'hp6_27',
         'hp6_18',
         'hp6_11',
         'hp6_16',
         'hp6_29',
         'hp6_17',
         'hp6_28',
         'hp6_10',
         'hp6_26',
         'hp6_19',
         'hp6_21',
         'hp6_8',
         'hp6_6',
         'hp6_1',
         'hp6_7',
         'hp6_9',
         'hp6_30',
         'hp6_24',
         'hp6_23',
         'hp6_15',
         'hp6_12',
         'hp6_13',
         'hp6_14',
         'hp6_22',
         'hp6_25',
         'hp7_34',
         'hp7_33',
         'hp7_32',
         'hp7_35',
         'hp7_1',
         'hp7_6',
         'hp7_8',
         'hp7_17',
         'hp7_28',
         'hp7_10',
         'hp7_26',
         'hp7_19',
         'hp7_21',
         'hp7_9',
         'hp7_7',
         'hp7_20',
         'hp7_27',
         'hp7_18',
         'hp7_11',
         'hp7_16',
         'hp7_29',
         'hp7_30',
         'hp7_36',
         'hp7_31',
         'hp7_13',
         'hp7_14',
         'hp7_22',
         'hp7_25',
         'hp7_5',
         'hp7_2',
         'hp7_24',
         'hp7_23',
         'hp7_15',
         'hp7_12',
         'hp7_3',
         'hp7_4']
#   jobs = ['test1','test2','test3','test4','testtext','test1','test2']
    machines = ["http://35.229.88.233:5000/job", "http://35.190.137.170:5000/job", "http://35.196.226.39:5000/job", "http://35.185.15.96:5000/job", "http://35.196.20.249:5000/job"]
    runjob(jobs, machines)

if __name__ == '__main__':
    main()
