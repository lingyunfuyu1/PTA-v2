#!/usr/bin/env python
# coding:utf-8

"""
Created on 20161208
Updated on 20161230
Updated on 20160324

@author: hzcaojianglong
"""

import logging
import os

import matplotlib

matplotlib.use('Agg')
from matplotlib import pyplot
from matplotlib.ticker import MultipleLocator


def draw_runtime_chart_check(result_dict):
    if not result_dict or isinstance(result_dict, dict):
        logging.warn('This "result_dict" is illegal!')
        return False
    testcase_name = result_dict.get("testcase_name")
    # 时间秒数列表、每秒通过数列表、每秒错误数列表为空时，无法绘制折线图
    time_since_unique_list = result_dict.get("time_since_unique_list")
    pass_sum_list = result_dict.get("pass_sum_list")
    error_sum_list = result_dict.get("error_sum_list")
    test_sum_list = result_dict.get("test_sum_list")
    if "-" in [time_since_unique_list, pass_sum_list, error_sum_list, test_sum_list]:
        message_info = "Required parameters are missing! Unable to draw the chart!"
        params_info = "[testcase_name=%s, time_since_unique_list=%s, pass_sum_list=%s, error_sum_list=%s, test_sum_list=%s]" % (
            testcase_name, time_since_unique_list, pass_sum_list, error_sum_list, test_sum_list)
        logging.error(message_info + " " + params_info)
        return False
    # 点列只有一个元素（即一个点）的时，无法绘制折线图，三个列表长度必然相等，这里只判断一个即可
    if len(time_since_unique_list) == 1 or len(pass_sum_list) == 1 or len(error_sum_list) == 1 or len(test_sum_list) == 1:
        message_info = "Some lists have only one point! Unable to draw the chart!"
        params_info = "[testcase_name=%s, len(time_since_unique_list)=%d, len(pass_sum_list)=%d ,len(error_sum_list)=%d, len(test_sum_list)=%d]" % (
            testcase_name, len(time_since_unique_list), len(pass_sum_list), len(error_sum_list), len(test_sum_list))
        logging.error(message_info + " " + params_info)
        return False
    return True


def draw_runtime_chart(result_dict, chart_dir_path, chart_file_name="report-runtime.png"):
    """
    根据性能测试运行时过程数据绘制图表
    :param result_dict:
    :param chart_dir_path:
    :param chart_file_name:
    :return:
    """
    if not draw_runtime_chart_check:
        logging.error('draw_runtime_chart_check FAILED!')
        return
    if not os.path.exists(chart_dir_path):
        logging.error('The parameter "chart_file_path" does not exist! [%s]' % chart_dir_path)
        return
    testcase_name = result_dict.get("testcase_name")
    time_since_unique_list = result_dict.get("time_since_unique_list")
    pass_sum_list = result_dict.get("pass_sum_list")
    error_sum_list = result_dict.get("error_sum_list")
    avg_rt_list = result_dict.get("avg_rt_list")
    max_rt_list = result_dict.get("max_rt_list")
    # 绘制折线图
    pass_sum_flag = 'b-'
    error_sum_flag = 'r-'
    avg_rt_flag = 'g-'
    max_rt_flag = 'y-'
    # 画折线图
    figure = pyplot.figure()
    # 设置标题
    pyplot.title("[Runtime]: " + testcase_name)
    # 网格效果
    pyplot.grid(True)
    ax1 = figure.add_subplot(111)
    ax2 = ax1.twinx()
    ax1.set_xlabel("Time (Time Since Starting in s)")
    ax1.set_ylabel("TPS/ERROR")
    ax2.set_ylabel("AVG_RT/MAX_RT (in ms)")
    pass_label = "TPS"
    error_label = "ERROR"
    avgrt_label = "AVG_RT"
    maxrt_label = "MAX_RT"
    ax1.plot(time_since_unique_list, error_sum_list, error_sum_flag, label=error_label)
    ax1.plot(time_since_unique_list, pass_sum_list, pass_sum_flag, label=pass_label)
    ax2.plot(time_since_unique_list, max_rt_list, max_rt_flag, label=maxrt_label)
    ax2.plot(time_since_unique_list, avg_rt_list, avg_rt_flag, label=avgrt_label)
    handles_pass_error, labels_pass_error = ax1.get_legend_handles_labels()
    legend1 = ax1.legend(handles_pass_error[::-1], labels_pass_error[::-1], loc="upper left")
    legend1.get_frame().set_alpha(0.5)
    handles_avgrt_maxrt, labels_avgrt_maxrt = ax2.get_legend_handles_labels()
    legend2 = ax2.legend(handles_avgrt_maxrt[::-1], labels_avgrt_maxrt[::-1], loc="upper right")
    legend2.get_frame().set_alpha(0.5)
    # 保存为文件
    pyplot.savefig(os.sep.join([chart_dir_path, chart_file_name]))
    # 清空，避免影响下次
    pyplot.cla()


def draw_comparison_chart(x_list, y_list, title, chart_file_path, chart_file_name="report-tps-compare.png"):
    """
        从Grinder运行日志目录的日志文件提取性能测试详细过程数据，并绘制图表
        :param x_list:
        :param y_list:
        :param title:
        :param chart_file_path:
        :param chart_file_name:
        :return:
        """
    if not isinstance(x_list, list):
        logging.error('The parameter "x_list" is not a list! [%s]' % x_list)
        return
    if len(x_list) == 0:
        logging.error('The parameter "x_list" is blank! [%s]' % x_list)
        return
    if not isinstance(y_list, list):
        logging.error('The parameter "y_list" is not a list! [%s]' % y_list)
        return
    if len(y_list) == 0:
        logging.error('The parameter "y_list" is blank! [%s]' % y_list)
        return
    if not os.path.exists(chart_file_path):
        logging.error('The parameter "chart_file_path" does not exist! [%s]' % chart_file_path)
        return
    # 画折线图
    figure = pyplot.figure()
    # 设置标题
    pyplot.title("[TPS Compare]: " + title)
    # 网格效果
    pyplot.grid(True)
    ax = figure.add_subplot(111)
    ax.set_xlabel("Time")
    ax.set_ylabel("TPS")
    tps_label = "TPS"
    xlocator = MultipleLocator(1)
    # y_zero_count = len(str(max(y_list)).split(".")[0])
    # ylocator = MultipleLocator(10 ** (y_zero_count - 1))
    x_list_tmp = [i + 1 for i in range(len(x_list))]
    xmin = min(x_list_tmp) - 1
    xmax = max(x_list_tmp) + 1
    x_list.insert(0, "")
    x_list.insert(0, "")
    x_list.append("")
    x_list.append("")
    # ymin = (int(0.8 * min(y_list))) / (10 ** (y_zero_count - 1)) * (10 ** (y_zero_count - 1))
    # ymax = (int(1.2 * max(y_list)) + 1) / (10 ** (y_zero_count - 1)) * (10 ** (y_zero_count - 1))
    pyplot.plot(x_list_tmp, y_list, 'b-o', label=tps_label)
    handles_tps, labels_tps = ax.get_legend_handles_labels()
    legend = ax.legend(handles_tps[::-1], labels_tps[::-1], loc="upper left")
    legend.get_frame().set_alpha(0.5)
    ax.xaxis.set_major_locator(xlocator)
    # ax.yaxis.set_major_locator(ylocator)
    pyplot.xlim(xmin, xmax)
    # pyplot.ylim(ymin, ymax)
    ax.set_xticklabels(x_list, rotation=15)
    # pyplot.subplots_adjust(left=None, bottom=0.2, right=None, top=None, wspace=None, hspace=None)
    # 保存为文件
    figure.set_size_inches(8.0, 6.0)
    figure.savefig('test2png.png', dpi=100)
    pyplot.savefig(os.sep.join([chart_file_path, chart_file_name]))
    # 清空，避免影响下次
    pyplot.cla()


def test1():
    result_directory = "result"
    mode = "test"
    testcase_dirname = "http_local-20170315134401"
    work_directory = os.sep.join([result_directory, mode, testcase_dirname])
    # 提取单个用例的一条测试结果数据
    from report_dict import collect_testing_result
    result_dict = collect_testing_result(work_directory)
    chart_dir_path = work_directory
    draw_runtime_chart(result_dict, chart_dir_path)


def test2():
    x_list = ["2017-03-01\n00:00:00", "2017-03-08\n00:00:00", "2017-03-15\n00:00:00", "2017-03-22\n00:00:00"]
    y_list = [110.0, 120.0, 115.0, 130.0]
    chart_file_path = "result"
    draw_comparison_chart(x_list, y_list, "test-title", chart_file_path, chart_file_name="report-tps.png")

if __name__ == '__main__':
    test2()
    pass
