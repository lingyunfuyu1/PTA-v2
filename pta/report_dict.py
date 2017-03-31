#!/usr/bin/env python
# coding:utf-8

"""
Created on 20161208
Updated on 20161230

@author: hzcaojianglong
"""

import logging
import math
import os
import re
import time


def _collect_info_from_main_log(grinder_main_log_file):
    """
    从The Grinder主日志文件收集测试结果数据，将收集到的数据保存到字典
    :param grinder_main_log_file: The Grinder主日志文件
    :return: result_dict_main主日志结果字典
    """
    # 构造字典保存结果信息
    key_list = ["testcase_name", "vuser_number", "tps", "mrt", "time_standard_deviation", "test_success", "test_failure"]
    result_dict_main = dict().fromkeys(key_list, "-")
    # 判断日志文件是否存在
    if not os.path.exists(grinder_main_log_file):
        return result_dict_main
    # 提取测试用例名称、成功次数、失败次数、平均响应时间、TPS、并发数
    # 测试用例名称。这里用文件名，不用脚本里的测试名称，主要是为了避免脚本忘记改测试名称，出现重复。
    # TODO: 脚本文件名也有重复的可能性，怎么保证唯一呢？小概率事件，主要靠制定规范约束吧。
    pattern_1 = re.compile(r'running "(.*?).py"')
    # 并发数。这里用关键信息thread-(.*?): starting, will run forever匹配启动的线程所在行
    pattern_2 = re.compile(r'thread-(.*?): starting, will')
    # TODO:用count控制搜索虚拟用户的次数，提高搜索效率，和并发数多少以及日志内容有关，设置查找前10万行应该足够了
    count = 0
    # 将虚拟用户存到列表，统计长度得到并发数
    virtual_user_list = []
    # 成功次数、失败次数、平均响应时间、TPS
    pattern_3 = re.compile(r'Totals\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+.*?')
    # 统一进行正则匹配查找
    for line in open(grinder_main_log_file):  # TODO:需要大文件性能优化？
        if pattern_1.search(line):
            result_dict_main["testcase_name"] = pattern_1.findall(line)[0].split(os.sep)[-1]
        if count < 100000 and pattern_2.search(line):
            virtual_user_list.append(pattern_2.findall(line))
            count += 1
        if pattern_3.search(line):
            tmp = pattern_3.findall(line)[0]
            if tmp[0].isdigit():
                result_dict_main["test_success"] = int(tmp[0])
            if tmp[1].isdigit():
                result_dict_main["test_failure"] = int(tmp[1])
            if tmp[2].replace(".", "").isdigit():
                result_dict_main["mrt"] = float(tmp[2])
            if tmp[3].replace(".", "").isdigit():
                result_dict_main["time_standard_deviation"] = float(tmp[3])
            if tmp[4].replace(".", "").isdigit():
                result_dict_main["tps"] = float(tmp[4])
    if virtual_user_list:
        vuser_number = len(virtual_user_list)
        result_dict_main["vuser_number"] = vuser_number
    return result_dict_main


def _calculate_main_additional(result_dict_main):
    """
    根据主日志文件数据计算出一些附加数据，将计算得到的附加数据保存到字典
    :param result_dict_main:主日志结果字典
    :return: result_dict_main_additional主日志附加结果字典
    """
    # 构造字典保存附加结果信息
    key_list = ["test_total", "failure_rate"]
    result_dict_main_additional = dict().fromkeys(key_list, "-")
    # 判断日志文件是否存在
    if not result_dict_main:
        logging.error('The parameter "result_dict_main" cannot be empty!')
        return result_dict_main_additional
    testcase_name = result_dict_main.get("testcase_name", "-")
    # 计算测试次数
    test_success = result_dict_main.get("test_success", "-")
    test_failure = result_dict_main.get("test_failure", "-")
    if isinstance(test_success, int) and test_success >= 0 and isinstance(test_failure, int) and test_failure >= 0:
        test_total = test_success + test_failure
        result_dict_main_additional["test_total"] = test_total
    else:
        message_info = "Required parameter error! Failed to calculate test_total!"
        params_info = "[testcase_name=%s, test_success=%s, test_failure=%s]" % (
            testcase_name, test_success, test_failure)
        logging.warn(message_info + " " + params_info)
    # 计算失败率
    test_total = result_dict_main_additional.get("test_total", "-")
    if isinstance(test_failure, int) and test_failure >= 0 and isinstance(test_total, int) and test_total > 0:
        failure_rate = round(test_failure / float(test_total), 4)
        result_dict_main_additional["failure_rate"] = failure_rate
    else:
        message_info = "Required parameter error! Failed to calculate failure_rate!"
        params_info = "[testcase_name=%s, test_failure=%s, test_total=%s]" % (
            testcase_name, test_failure, test_total)
        logging.warn(message_info + " " + params_info)
    return result_dict_main_additional


def _collect_info_from_data_log(grinder_data_log_file):
    """
    从The Grinder数据日志文件收集测试结果数据，将收集到的数据保存到字典
    :param grinder_data_log_file: The Grinder数据日志文件
    :return: result_dict_data数据日志结果字典
    """
    # 构造字典保存结果信息
    key_list = ["thread_list", "run_list", "start_time_list", "time_since_list", "time_format_list", "test_list", "error_list", "test_time_list"]
    result_dict_data = dict().fromkeys(key_list, "-")
    # 判断日志文件是否存在
    if not os.path.exists(grinder_data_log_file):
        return result_dict_data
    # 开始时间列表、响应时间列表
    # Thread, Run, Test, Start time(ms since Epoch), Test time, Errors
    # 0, 0, 1, 1489556960661, 91, 0
    # 0, 1, 1, 1489556960754, 104, 1
    #
    # Thread, Run, Test, Start time(ms since Epoch), Test time, Errors, HTTP response code, HTTP response length, HTTP response errors, Time to resolve host, Time to establish connection, Time to first byte, New connections
    # 0, 0, 1, 1489549968209, 414, 0, 200, 640, 0, 0, 6, 340, 1
    # 7, 0, 1, 1489549968209, 414, 0, 200, 640, 0, 0, 4, 326, 1
    # pattern里要提取的数据为Test, Start time(ms since Epoch), Test time, Errors
    pattern = re.compile(r"(\d*?),\s(\d*?),\s(\d*?),\s(\d*?),\s(\d*?),\s(\d*?)[\s,]")
    tmp_list = []
    for line in open(grinder_data_log_file):
        if not pattern.search(line):
            continue
        tmp = pattern.findall(line)[0]
        tmp_list.append('|'.join([tmp[3], tmp[0], tmp[1], tmp[2], tmp[5], tmp[4]]))
    # 这里根据时间字段对数据行做了排序，因为有些时间先后顺序是反的；如果不排序，后续计算附加数据会有影响
    tmp_list.sort()
    start_time_list = []
    time_since_list = []
    time_format_list = []
    thread_list = []
    run_list = []
    test_list = []
    error_list = []
    test_time_list = []
    for tmp in tmp_list:
        tmp_parts = tmp.split('|')
        start_time_list.append(int(tmp_parts[0]))
        # 计算测试时间线1，从开始到现在过去多久，单位为秒。如测试10分钟，则数据为0-600
        time_since = int(tmp_parts[0]) / 1000 - start_time_list[0] / 1000
        time_since_list.append(time_since)
        # 计算测试时间线2，当前时刻的标准格式
        time_format = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(tmp_parts[0]) / 1000))
        time_format_list.append(time_format)
        thread_list.append(int(tmp_parts[1]))
        run_list.append(int(tmp_parts[2]))
        test_list.append(int(tmp_parts[3]))
        error_list.append(int(tmp_parts[4]))
        test_time_list.append(int(tmp_parts[5]))
    result_dict_data["start_time_list"] = start_time_list
    result_dict_data["time_since_list"] = time_since_list
    result_dict_data["time_format_list"] = time_format_list
    result_dict_data["thread_list"] = thread_list
    result_dict_data["run_list"] = run_list
    result_dict_data["test_list"] = test_list
    result_dict_data["error_list"] = error_list
    result_dict_data["test_time_list"] = test_time_list
    return result_dict_data


def _calculate_data_additional(result_dict_data):
    """
    根据主日志文件数据计算出一些附加数据，将计算得到的附加数据保存到字典
    :param result_dict_data:数据日志结果字典
    :return: result_dict_data_additional数据日志附加结果字典
    """
    # 构造字典保存附加结果信息
    key_list = ["rt_50", "rt_90", "rt_99", "time_since_unique_list", "test_sum_list", "error_sum_list", "pass_sum_list", "avg_rt_list", "max_rt_list", "execute_time"]
    result_dict_data_additional = dict().fromkeys(key_list, "-")
    if not result_dict_data:
        logging.error('The parameter "result_dict_data" cannot be empty!')
        return result_dict_data_additional
    # 计算50%、90%、99%的响应时间
    test_time_list = result_dict_data.get("test_time_list", "-")
    if isinstance(test_time_list, list):
        # 此段代码慎改，建议用少量数据边测试边修改
        test_time_list_sorted = sorted(test_time_list)
        rt_list_length = len(test_time_list_sorted)
        index_50 = int(math.ceil(rt_list_length / 2.0))
        result_dict_data_additional["rt_50"] = test_time_list_sorted[index_50 - 1]
        index_90 = int(math.ceil(rt_list_length * 9 / 10.0))
        result_dict_data_additional["rt_90"] = test_time_list_sorted[index_90 - 1]
        index_99 = int(math.ceil(rt_list_length * 99 / 100.0))
        result_dict_data_additional["rt_99"] = test_time_list_sorted[index_99 - 1]
    else:
        message_info = "Required parameter error! Failed to calculate 50percentRT、90percentRT、99percentRT!"
        params_info = "[test_time_list=%s]" % test_time_list
        logging.warn(message_info + " " + params_info)
    # 计算每秒钟测试个数、通过个数、错误个数，测试个数=通过个数+失败个数
    time_since_list = result_dict_data.get("time_since_list", "-")
    test_list = result_dict_data.get("test_list", "-")
    error_list = result_dict_data.get("error_list", "-")
    test_time_list = result_dict_data.get("test_time_list", "-")
    if isinstance(time_since_list, list) and isinstance(test_list, list) and isinstance(error_list, list) and isinstance(test_time_list, list):
        time_since_unique_list = []
        test_sum_list = []
        error_sum_list = []
        pass_sum_list = []
        avg_rt_list = []
        max_rt_list = []
        time_since_tmp = time_since_list[0]
        time_since_unique_list.append(time_since_tmp)
        test_sum = 0
        error_sum = 0
        pass_sum = 0
        time_sum = 0
        time_sum_max = 0
        count = 0
        for i in range(len(time_since_list)):
            if time_since_list[i] == time_since_tmp:
                test_sum += test_list[i]
                error_sum += error_list[i]
                pass_sum += (test_list[i] - error_list[i])
                time_sum += test_time_list[i]
                time_sum_max = max(time_sum_max, test_time_list[i])
                count += 1
            else:
                time_since_tmp = time_since_list[i]
                time_since_unique_list.append(time_since_tmp)
                test_sum_list.append(test_sum)
                error_sum_list.append(error_sum)
                pass_sum_list.append(pass_sum)
                avg_rt_list.append(time_sum / count)
                max_rt_list.append(time_sum_max)
                test_sum = test_list[i]
                error_sum = error_list[i]
                pass_sum = (test_list[i] - error_list[i])
                time_sum = test_time_list[i]
                time_sum_max = test_time_list[i]
                count = 1
        test_sum_list.append(test_sum)
        error_sum_list.append(error_sum)
        pass_sum_list.append(pass_sum)
        avg_rt_list.append(time_sum / count)
        max_rt_list.append(time_sum_max)
        # 四个列表最终长度一样，应该等于运行的秒数
        result_dict_data_additional["time_since_unique_list"] = time_since_unique_list
        result_dict_data_additional["test_sum_list"] = test_sum_list
        result_dict_data_additional["error_sum_list"] = error_sum_list
        result_dict_data_additional["pass_sum_list"] = pass_sum_list
        result_dict_data_additional["avg_rt_list"] = avg_rt_list
        result_dict_data_additional["max_rt_list"] = max_rt_list
        # 选择最小的格式化时间作为执行时间
        result_dict_data_additional["execute_time"] = min(result_dict_data.get("time_format_list"))
    return result_dict_data_additional


def collect_testing_result(grinder_log_directory):
    """
    根据The Grinder的日志目录，收集The Grinder的测试结果数据，将得到的数据保存到字典
    :param grinder_log_directory:根据The Grinder的日志目录
    :return: result_dict测试结果字典
    """
    if not grinder_log_directory:
        logging.error('The parameter "grinder_log_directory" cannot be empty!')
        return
    grinder_main_log_file = os.sep.join([grinder_log_directory, "PTA-main.log"])
    grinder_data_log_file = os.sep.join([grinder_log_directory, "PTA-data.log"])
    if not os.path.exists(grinder_main_log_file) or not os.path.exists(grinder_data_log_file):
        logging.error("The grinder log files are not found! [PTA-main.log or PTA-data.log]")
        return
    # 提取主日志中的结果数据，保存到字典result_dict_main
    result_dict_main = _collect_info_from_main_log(grinder_main_log_file)
    # 根据主日志数据计算附加数据，保存到字典result_dict_main_additional
    result_dict_main_additional = _calculate_main_additional(result_dict_main)
    # 提取数据日志中的结果数据，保存到字典result_dict_data
    result_dict_data = _collect_info_from_data_log(grinder_data_log_file)
    # 根据数据日志数据计算附加数据，保存到字典result_dict_data_additional
    result_dict_data_additional = _calculate_data_additional(result_dict_data)
    # 合并4个结果字典，得到最终结果字典
    result_dict = {}
    result_dict.update(result_dict_main)
    result_dict.update(result_dict_main_additional)
    result_dict.update(result_dict_data)
    result_dict.update(result_dict_data_additional)
    # 根据完整的测试结果数据做结果评估
    result_dict_risk = assess_risk(result_dict)
    # 将评估结果追加到测试结果数据中
    result_dict.update(result_dict_risk)
    return result_dict


def assess_risk(result_dict):
    key_list = ["status", "note"]
    result_dict_risk = dict().fromkeys(key_list, "-")
    if not result_dict:
        logging.error('The parameter "result_dict" cannot be empty!')
        result_dict_risk["status"] = "0000"
        result_dict_risk["note"] = "没有可评估的数据；"
        return result_dict_risk
    else:
        result_dict_risk["status"] = "0000"
        note = ""
    if "-" in result_dict.values():
        result_dict_risk["status"] = "0000"
        note += "结果数据缺失；"
    if result_dict.get("failure_rate", 0) >= 0.01:
        result_dict_risk["status"] = "0000"
        note += "失败率过高；"
    if result_dict.get('time_standard_deviation', 0) / result_dict.get("mrt", 1) >= 0.2:
        result_dict_risk["status"] = "0000"
        note += "TPS-RT曲线波动太大；"
    result_dict_risk["note"] = note
    return result_dict_risk


def test():
    result_directory = "result"
    mode = "test"
    testcase_dirname = "pay_trade_service-20170315114007"
    # 提取测试结果数据
    result_dict = collect_testing_result(os.sep.join([result_directory, mode, testcase_dirname]))
    for key, value in result_dict.items():
        print key, ': ', value


if __name__ == '__main__':
    test()
    pass
