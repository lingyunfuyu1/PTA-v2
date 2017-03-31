#!/usr/bin/env python
# coding:utf-8

"""
Created on 20161208
Updated on 20161230

@author: hzcaojianglong
"""

import logging
import os


def _get_html_content(table_content):
    html_content = """
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html" ;charset="utf-8" />
        </head>
        <body>
            <h3>性能测试报告如下（上面为数据表格、下面为运行过程图和TPS趋势图）：</h3>
            <table border="1" cellspacing="0" cellpadding="0" style="border-collapse:collapse;" align="left">
            %s
            </table>
        </body>
    </html>
    """ % table_content
    return html_content


def _get_table_content_title():
    table_content_title = """
    <tr bgcolor="DarkGray">
        <td>
            <b>
                测试用例
            </b>
        </td>
        <td>
            <b>
                测试执行时间
            </b>
        </td>
        <td>
            <b>
                并发数
            </b>
        </td>
        <td>
            <b>
                测试时长(s)
            </b>
        </td>
        <td>
            <b>
                TPS
            </b>
        </td>
        <td>
            <b>
                MRT(ms)
            </b>
        </td>
        <td>
            <b>
                50%RT(ms)
            </b>
        </td>
        <td>
            <b>
                90%RT(ms)
            </b>
        </td>
        <td>
            <b>
                99%RT(ms)
            </b>
        </td>
        <td>
            <b>
                测试次数
            </b>
        </td>
        <td>
            <b>
                成功次数
            </b>
        </td>
        <td>
            <b>
                失败次数
            </b>
        </td>
        <td>
            <b>
                失败率
            </b>
        </td>
    </tr>
    """
    return table_content_title


def _get_table_content_data(result_dict, need_show_risk=False):
    """
    从Grinder运行日志目录的日志文件提取性能测试数据，生成html格式报告
    :param result_dict:
    :return:
    """
    if not result_dict or not isinstance(result_dict, dict):
        logging.error('The parameter "result_dict" is empty! Unable to generate html table content!')
        return
    table_content_data = "<tr>"
    table_content_data += "<td><b>%s</b></td>" % result_dict.get("testcase_name")
    table_content_data += "<td>%s</td>" % result_dict.get("execute_time")
    table_content_data += "<td>%s</td>" % result_dict.get("vuser_number")
    table_content_data += "<td>%s</td>" % result_dict.get("time_since_list")[-1]
    table_content_data += "<td>%s</td>" % result_dict.get("tps")
    table_content_data += "<td>%s</td>" % result_dict.get("mrt")
    table_content_data += "<td>%s</td>" % result_dict.get("rt_50")
    table_content_data += "<td>%s</td>" % result_dict.get("rt_90")
    table_content_data += "<td>%s</td>" % result_dict.get("rt_99")
    table_content_data += "<td>%s</td>" % result_dict.get("test_total")
    table_content_data += "<td>%s</td>" % result_dict.get("test_success")
    table_content_data += "<td>%s</td>" % result_dict.get("test_failure")
    failure_rate = result_dict.get("failure_rate")
    if isinstance(failure_rate, float):
        table_content_data += "<td>%s</td>" % format(failure_rate, '0.2%')
    else:
        table_content_data += "<td>%s</td>" % failure_rate
    table_content_data += "</tr>"
    if need_show_risk:
        table_content_data += """
        <tr>
            <td colspan="13">
                <b>
                    风险评估：
                </b>
                <font color="red">
                    %s
                </font>
            </td>
        </tr>
        """ % result_dict.get("note", "无")
    return table_content_data


def generate_html_report(result_dict, need_show_risk):
    """
    根据某一测试用例的单次测试结果数据，生成html格式的报告
    :param result_dict:某一测试用例的单次测试结果数据
    :param need_show_risk:
    :return:html格式的报告
    """
    table_content_title = _get_table_content_title()
    table_content_data = _get_table_content_data(result_dict, need_show_risk)
    table_content = table_content_title + table_content_data
    html_report = _get_html_content(table_content)
    return html_report


def generate_html_report_batch(result_dict_list, need_show_risk):
    """
    根据多个测试用例的测试结果数据，生成html格式的报告
    :param result_dict_list:多个测试用例的测试结果数据组成的列表
    :param need_show_risk:
    :return:html格式的报告
    """
    table_blank_row = """
    <tr>
        <td colspan="13">
            </br>
        </td>
    </tr>
    """
    table_content_title = _get_table_content_title()
    if need_show_risk:
        table_content = ""
        for result_dict in result_dict_list:
            table_content_data = _get_table_content_data(result_dict, need_show_risk)
            table_content += table_content_title + table_content_data + table_blank_row
    else:
        table_content = table_content_title
        for result_dict in result_dict_list:
            table_content_data = _get_table_content_data(result_dict, need_show_risk)
            table_content += table_content_data
    html_report = _get_html_content(table_content)
    return html_report


def generate_html_report_compare(result_dict_list, need_show_risk):
    """
    根据某一测试用例的多次测试结果数据，生成html格式的对比报告
    :param result_dict_list:同一测试用例的多次测试结果数据组成的列表，注意按时间顺序排列，最后一个是最新的
    :param need_show_risk:
    :return: html格式的对比报告
    """
    testcase_name = result_dict_list[-1].get("testcase_name")
    for result_dict in result_dict_list:
        if result_dict.get("testcase_name") != testcase_name:
            logging.error('It seems that "result_dict_list" contains different test cases. No support for comparing.')
            return
    table_content_title = _get_table_content_title()
    table_content = table_content_title
    for index in range(len(result_dict_list)):
        if index != len(result_dict_list) - 1:
            table_content_data = _get_table_content_data(result_dict_list[index], False)
        else:
            table_content_data = _get_table_content_data(result_dict_list[index], need_show_risk)
        table_content += table_content_data
    html_report = _get_html_content(table_content)
    return html_report


def save_html_report_to_file(html_report, html_dir_path, html_file_name="report.html"):
    with open(os.sep.join([html_dir_path, html_file_name]), 'w') as result_file:
        result_file.write(html_report)


def test1():
    result_directory = "result"
    mode = "test"
    test_id = "20170327100047"
    testcase_name_unique = "1-call_java_method"
    work_directory = os.sep.join([result_directory, mode, test_id, testcase_name_unique])
    # 提取单个用例的一条测试结果数据
    from report_dict import collect_testing_result
    result_dict = collect_testing_result(work_directory)
    # 生成该用例的报告
    html_report = generate_html_report(result_dict, False)
    # 保存html报告
    html_dir_path = work_directory
    save_result_to_html_report(html_report, html_dir_path)
    pass


def test2():
    result_directory = "result"
    mode = "test"
    test_id = "20170327100047"
    # 提取各个用例的测试结果数据
    from report_dict import collect_testing_result
    result_dict_list = []
    for testcase_name_unique in ["1-call_java_method", "2-helloworld", ]:
        work_directory = os.sep.join([result_directory, mode, test_id, testcase_name_unique])
        result_dict = collect_testing_result(work_directory)
        result_dict_list.append(result_dict)
    # 生成多个测试用例的汇总报告
    html_report = generate_html_report_batch(result_dict_list, False)
    # 保存html报告
    html_dir_path = os.sep.join([result_directory, mode])
    save_result_to_html_report(html_report, html_dir_path, "summary-report.html")
    pass


def test3():
    result_directory = "result"
    mode = "test"
    testcase_name_unique = "1-call_java_method"
    test_id = "20170327100047"
    # 提取各个用例的测试结果数据
    from report_dict import collect_testing_result
    result_dict_list = []
    for test_id in ["20170327100047", "20170327100536", "20170327101100"]:
        work_directory = os.sep.join([result_directory, mode, test_id, testcase_name_unique])
        result_dict = collect_testing_result(work_directory)
        result_dict_list.append(result_dict)
    # 生成该用例的多条记录比对报告
    html_report = generate_html_report_compare(result_dict_list, False)
    # 保存html报告
    html_dir_path = work_directory
    save_result_to_html_report(html_report, html_dir_path)
    pass


if __name__ == '__main__':
    test1()
    test2()
    test3()
    pass
