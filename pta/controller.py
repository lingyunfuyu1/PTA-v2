#!/usr/bin/env python
# coding:utf-8

"""
Created on 20161123
Updated on 20161230

@author: xh
"""
import logging
import os
import tarfile
import time

from PIL import Image

import engine
import mail
import report_chart
import report_dict
import report_html
import report_json


def _get_task_dict_list(task_file):
    # 获取任务信息
    if not os.path.exists(task_file):
        logging.error("No such file! [%s]" % task_file)
        return
    task_dict_list = []
    count = 0
    for line in open(task_file):
        line = line.strip()
        if line.startswith("#"):
            continue
        if line.count("|") != 3:
            logging.error("Invalid configuration! Skipped! [%s]" % line.strip())
            continue
        count += 1
        tmp = line.split("|")
        task_dict = {"script_file": tmp[0].strip(),
                     "testcase_name": os.path.splitext(os.path.basename(tmp[0].strip()))[0],
                     "grinder_threads": int(tmp[1].strip()),
                     "grinder_duration": int(tmp[2].strip()),
                     "grinder_runs": int(tmp[3].strip())}
        task_dict["testcase_name_unique"] = str(count) + "-" + task_dict.get("testcase_name")
        task_dict_list.append(task_dict)
    return task_dict_list


def _run_and_collect(task_dict, mode, test_id, result_directory):
    # 执行测试
    testcase_name_unique = task_dict.get("testcase_name_unique")
    testcase_name = task_dict.get("testcase_name")
    script_file = task_dict.get("script_file")
    lib_directory = os.path.dirname(task_dict.get("script_file"))
    log_directory = os.sep.join([result_directory, mode, test_id, task_dict.get("testcase_name_unique")])
    grinder_threads = task_dict.get("grinder_threads")
    grinder_duration = task_dict.get("grinder_duration")
    grinder_runs = task_dict.get("grinder_runs")
    engine.generate_grinder_properties_file(script_file, lib_directory=lib_directory, log_directory=log_directory,
                                            grinder_threads=grinder_threads, grinder_duration=grinder_duration,
                                            grinder_runs=grinder_runs)
    logging.info("[Task: %s] engine.run_testing() is starting..." % testcase_name_unique)
    engine.run_testing()
    logging.info("[Task: %s] engine.run_testing() is finished." % testcase_name_unique)
    # 提取当次测试结果
    logging.info("[Task: %s] collect_testing_result is starting..." % testcase_name_unique)
    result_dict = report_dict.collect_testing_result(log_directory)
    logging.info("[Task: %s] collect_testing_result is finished..." % testcase_name_unique)
    # 测试结果持久化存储到json文件
    report_json.save_result_to_json_report(result_dict, log_directory)
    # 记录任务执行信息
    record_file = open(os.sep.join([result_directory, mode, "record.txt"]), 'a')
    record_file.write(testcase_name + "|" + log_directory + "|\n")
    record_file.close()
    # 生成一份html报告，方便查看结果
    html_report = report_html.generate_html_report(result_dict, need_show_risk=True)
    report_html.save_html_report_to_file(html_report, log_directory)
    # 绘制运行时图表报告
    report_chart.draw_runtime_chart(result_dict, log_directory)
    return result_dict


def run_and_collect_batch(task_file, mode, test_id, result_directory):
    task_dict_list = _get_task_dict_list(task_file)
    # 执行测试任务
    if not task_dict_list or not isinstance(task_dict_list, list):
        logging.error("No tasks! Please check the task file. [%s]" % task_dict_list)
        return
    result_dict_list = []
    for task_dict in task_dict_list:
        try:
            result_dict = _run_and_collect(task_dict, test_id)
            result_dict_list.append(result_dict)
        except Exception as e:
            logging.exception("Exception occurred when performing task! [%s]" % task_dict.get("testcase_name_unique"))
    # 生成该批次用例的汇总报告
    html_report = report_html.generate_html_report_batch(result_dict_list, need_show_risk=True)
    report_html.save_html_report_to_file(html_report, os.sep.join([result_directory, mode, test_id]),
                                         html_file_name="batch-report.html")
    # 发送邮件
    work_directory = os.sep.join([result_directory, mode, test_id])
    send_mail_report(work_directory, mode)


def run_and_collect_compare(task_file, mode, test_id, result_directory):
    task_dict_list = _get_task_dict_list(task_file)
    # 执行测试任务
    if not task_dict_list or not isinstance(task_dict_list, list):
        logging.error("No tasks! Please check the task file. [%s]" % task_dict_list)
        return
    result_dict_list = []
    for task_dict in task_dict_list:
        try:
            result_dict = _run_and_collect(task_dict, test_id)
            result_dict_list.append(result_dict)
        except Exception as e:
            logging.exception("Exception occurred when performing task! [%s]" % task_dict.get("testcase_name_unique"))
    # 生成该批次测试的比对报告
    html_report = report_html.generate_html_report_compare(result_dict_list, need_show_risk=True)
    report_html.save_html_report_to_file(html_report, os.sep.join([result_directory, mode, test_id]),
                                         html_file_name="compare-report.html")
    # 发送邮件
    work_directory = os.sep.join([result_directory, mode, test_id])
    send_mail_report(work_directory, mode)


def run_and_collect_compare_batch(task_file, mode, test_id, result_directory):
    task_dict_list = _get_task_dict_list(task_file)
    # 执行测试任务
    if not task_dict_list or not isinstance(task_dict_list, list):
        logging.error("No tasks! Please check the task file. [%s]" % task_dict_list)
        return
    result_dict_list = []
    for task_dict in task_dict_list:
        try:
            # 运行测试收集结果数据
            result_dict = _run_and_collect(task_dict, mode, test_id, result_directory)
            # 获取与历史结果的比对数据
            result_dict_tps_compare = get_tps_compare_result(task_dict, mode, result_directory)
            # 反写风险信息note，增加比对的风险判断
            note = result_dict.get("note")
            note_compare = result_dict_tps_compare.get("note_compare")
            if note_compare != "-":
                result_dict["note"] = note + note_compare
            # 保存到列表，用于后续生成html报告
            result_dict_list.append(result_dict)
            # 绘制tps比对图
            x_list = result_dict_tps_compare.get("execute_time_list")
            y_list = result_dict_tps_compare.get("tps_list")
            title = task_dict.get("testcase_name")
            chart_file_path = os.sep.join([result_directory, mode, test_id, task_dict.get("testcase_name_unique")])
            report_chart.draw_comparison_chart(x_list, y_list, title, chart_file_path)
            # 合并两个图片
            image_list = [os.sep.join([chart_file_path, "report-runtime.png"]),
                          os.sep.join([chart_file_path, "report-tps-compare.png"])]
            merged_chart_file_name = task_dict.get("testcase_name_unique") + ".png"
            toImage = Image.new('RGBA', (1600, 600))
            for i in range(len(image_list)):
                fromImge = Image.open(image_list[i])
                loc = ((i % 2) * 800, 0)
                toImage.paste(fromImge, loc)
                # os.remove(image_list[i])
            toImage.save(os.sep.join([result_directory, mode, test_id, merged_chart_file_name]))
        except Exception as e:
            logging.exception("Exception occurred when performing task! [%s]" % task_dict.get("testcase_name_unique"))
    # 生成该批次测试的比对报告
    html_report = report_html.generate_html_report_batch(result_dict_list, need_show_risk=True)
    report_html.save_html_report_to_file(html_report, os.sep.join([result_directory, mode, test_id]),
                                         html_file_name="summary-report.html")
    # 发送邮件
    work_directory = os.sep.join([result_directory, mode, test_id])
    send_mail_report(work_directory, mode)


def get_tps_compare_result(task_dict, mode, result_directory, history_number=3):
    # 构造字典保存结果信息
    key_list = ["testcase_name_unique", "execute_time_list", "tps_list", "note_compare"]
    result_dict_tps_compare = dict().fromkeys(key_list, "-")
    record_list = []
    for line in open(os.sep.join([result_directory, mode, "record.txt"])):
        if line.strip().startswith(task_dict.get("testcase_name")):
            record_list.append(line)
    if not record_list:
        logging.error("No records for this task! Skipped! [testcase_name=%s]" % task_dict.get("testcase_name"))
        return
    execute_time_list = []
    tps_list = []
    count = 0
    for record in record_list[-history_number - 1:]:
        count += 1
        json_dir_path = record.split("|")[1].strip()
        result_dict_tmp = report_json.get_result_from_json_report(json_dir_path)
        execute_time_list.append(result_dict_tmp.get("execute_time").replace(" ", "\n"))
        tps_list.append(result_dict_tmp.get("tps"))
    note_compare = ""
    if len(tps_list) > 1:
        tps_current = tps_list[-1]
        tps_old = tps_list[-2]
        if isinstance(tps_current, float) and isinstance(tps_old, float) and tps_old > 0.0 and (
            tps_old - tps_current) / float(tps_old) > 0.1:
            note_compare = "TPS比上次测试降低10%以上；"
    result_dict_tps_compare["testcase_name_unique"] = task_dict.get("testcase_name_unique")
    result_dict_tps_compare["execute_time_list"] = execute_time_list
    result_dict_tps_compare["tps_list"] = tps_list
    result_dict_tps_compare["note_compare"] = note_compare
    return result_dict_tps_compare


def send_mail_report(work_directory, mode):
    # #######发送邮件#######
    if mode == "test":
        receiver_list = ["hzcaojianglong@corp.netease.com", ]
    elif mode == "online":
        receiver_list = ["caojl01@gmail.com", "hzcaojianglong@corp.netease.com"]
    else:
        receiver_list = ["caojl01@gmail.com"]
    subject = u"性能测试自动化执行报告"
    # 邮件正文
    content = open(os.sep.join([work_directory, "summary-report.html"])).read()
    # 发送邮件
    logging.info("Sending email to %s" % str(receiver_list))
    image_list = []
    compressed_file = os.sep.join([work_directory, "图表报告.tgz"])
    tar = tarfile.open(compressed_file, 'w')
    for root, dir, files in os.walk(work_directory):
        for file in files:
            if file.endswith('.png') and not file.endswith('-tps-compare.png') and not file.endswith('-runtime.png'):
                fullpath = os.path.join(root, file)
                image_list.append(fullpath)
                tar.add(fullpath, arcname=file)
    tar.close()
    attachment_list = [compressed_file]
    mail.mail(receiver_list, subject, content, image_list=image_list, attachment_list=[],
              sender="pta_system@pta.server.org", _subtype="html")
    os.remove(compressed_file)


def test1():
    task_file = "task_list.txt"
    # run_and_collect_batch(task_dict_list, test_id=time.strftime("%Y%m%d%H%M%S", time.localtime()))
    # run_and_collect_compare(task_dict_list, test_id=time.strftime("%Y%m%d%H%M%S", time.localtime()))
    run_and_collect_compare_batch(task_file, test_id=time.strftime("%Y%m%d%H%M%S", time.localtime()))


if __name__ == "__main__":
    test1()
