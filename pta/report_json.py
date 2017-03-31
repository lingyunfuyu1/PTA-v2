#!/usr/bin/env python
# coding:utf-8

"""
Created on 20161208
Updated on 20161230

@author: hzcaojianglong
"""

import logging
import os
import simplejson


def save_result_to_json_report(result_dict, json_dir_path, json_file_name="report.json"):
    if not os.path.exists(json_dir_path):
        logging.error('The parameter "json_dir_path" does not exist! [%s]' % json_dir_path)
        return
    # 将测试结果写入json文件
    json_file_path = os.sep.join([json_dir_path, json_file_name])
    result_file = open(json_file_path, 'w')
    json_string = simplejson.dumps(result_dict, ensure_ascii=False, sort_keys=False, indent=4,
                                   separators=(',', ': ')).encode("utf-8")
    result_file.write(json_string)
    result_file.close()


def get_result_from_json_report(json_dir_path, json_file_name="report.json"):
    if not os.path.exists(json_dir_path):
        logging.error('The parameter "json_dir_path" does not exist! [%s]' % json_dir_path)
        return
    json_file = os.sep.join([json_dir_path, json_file_name])
    if not os.path.exists(json_file):
        logging.warn('The file "report.json" was not found! [%s]' % json_dir_path)
        return
    json_string = open(json_file, 'r').read()
    result_dict = simplejson.loads(json_string, encoding="utf-8")
    return result_dict


def test():
    result_directory = "result"
    mode = "test"
    testcase_dirname = "pay_trade_service-20170315114007"
    # 提取测试结果数据
    from report_dict import collect_testing_result
    result_dict = collect_testing_result(os.sep.join([result_directory, mode, testcase_dirname]))
    # 保存到json文件
    json_dir_path = os.sep.join([result_directory, mode, testcase_dirname])
    save_result_to_json_report(result_dict, json_dir_path)
    print '------------------------------'
    result_dict = get_result_from_json_report(json_dir_path)
    for key, value in result_dict.items():
        print key, ': ', value


if __name__ == '__main__':
    test()
    pass
