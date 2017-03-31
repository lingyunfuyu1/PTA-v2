#!/usr/bin/env python
# coding:utf-8
import logging
import os

import time
import controller

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(filename)s(%(lineno)d): %(funcName)s] PID-%(process)d %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=os.getcwd() + os.sep + "pta.log",
    filemode="a")
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("[%(levelname)s]  PID-%(process)d  %(funcName)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

mode = "test"

# if len(sys.argv) == 2 and sys.argv[1] in ["test", "online"]:
#     pass
# else:
#     print "Usage: %s [test|online]" % (sys.argv[0])
#     sys.exit(1)
# mode = sys.argv[1]

result_directory = "result"
task_file = "task_list.txt"


def run1(test_id):
    controller.run_and_collect_batch(task_file, mode, test_id, result_directory)


def run2(test_id):
    controller.run_and_collect_compare(task_file, mode, test_id, result_directory)


def run3(test_id):
    controller.run_and_collect_compare_batch(task_file, mode, test_id, result_directory)

if __name__ == "__main__":
    test_id = time.strftime("%Y%m%d%H%M%S", time.localtime())
    run3(test_id)
