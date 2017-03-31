#!/usr/bin/python
# coding:utf-8

"""
Created on 20161123
Updated on 20161230

@author: hzcaojianglong
"""
import logging
import os
import sys


def generate_grinder_properties_file(script_file, lib_directory="", log_directory="log", grinder_threads=1, grinder_duration=0, grinder_runs=1, grinder_properties_file="grinder.properties"):
    """
    更新grinder.properties文件，动态调整本次测试使用的脚本和并发数
    :return:
    """
    # 检查脚本是否存在
    script_file = os.path.abspath(script_file.strip())
    if not os.path.exists(script_file):
        logging.error("No such file! [script_file=%s]" % script_file)
        return
    # 检查依赖Jar目录是否存在，不存在后续使用时不影响
    lib_directory = os.path.abspath(lib_directory.strip())
    if not os.path.exists(lib_directory):
        logging.warn("No such directory! [lib_directory=%s]" % lib_directory)
    # 检查日志路径是否存在，不存在则自动创建
    log_directory = os.path.abspath(log_directory.strip())
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    # 检查属性值是否合理
    if not isinstance(grinder_threads, int) or grinder_threads <= 0:
        logging.error("This property must be an integer! [grinder_threads=%s]" % grinder_threads)
        return
    # # 并发数上限设置10000，避免并发数过大，导致客户端无法发起压力或者服务端无法承受压力。
    # if grinder_threads > 10000:
    #     logging.error(
    #         "grinder_threads should not be greater than 1000! [grinder_threads=%d]" % grinder_threads)
    #     sys.exit(1)
    if not isinstance(grinder_duration, int) or grinder_duration < 0:
        logging.error("This property must be an integer! [grinder_duration=%s]" % grinder_duration)
        return
    if not isinstance(grinder_runs, int) or grinder_runs < 0:
        logging.error("This property must be an integer! [grinder_runs=%s]" % grinder_runs)
        return
    if grinder_duration == 0 and grinder_runs == 0:
        message_info = "The properties of grinder_duration and grinder_runs should not be zero at the same time!"
        params_info = "[grinder_duration=%s, grinder_runs=%s]" % (grinder_duration, grinder_runs)
        logging.error(message_info + " " + params_info)
        return
    # 生成grinder.properties
    result_file = open(grinder_properties_file, 'w')
    result_file.write("grinder.useConsole = false\n")
    result_file.write(
        "grinder.logDirectory = %s\n" % log_directory.replace(os.sep, "/"))  # Grinder配置只支持/作为路径分隔符
    result_file.write("grinder.numberOfOldLogs = 7\n")  # 归档日志保留个数
    result_file.write("grinder.script = %s\n" % script_file.replace(os.sep, "/"))
    result_file.write("grinder.jvm.classpath = %s\n" % os.sep.join([lib_directory, "*"]).replace(os.sep, "/"))
    result_file.write("grinder.processes = 1\n")
    result_file.write("grinder.threads = %d\n" % grinder_threads)
    result_file.write("grinder.duration = %d\n" % (grinder_duration * 1000))
    result_file.write("grinder.runs = %d\n" % grinder_runs)
    result_file.close()


def run_testing(java_path="java", grinder_home="grinder-3.11", grinder_properties_file="grinder.properties"):
    """
    对各个实例变量进行检查，判断是否可用，所需依赖是否满足
    :return:
    """
    # 检查指定的java是否可用
    if java_path != "java":
        if not os.path.exists(java_path):
            logging.error("No such directory! [%s]" % java_path)
            sys.exit(1)
        else:
            java_path = os.path.abspath(java_path)
            java_path = '"' + java_path + '"'
    if os.name == "nt":
        null_device = "nul"
    elif os.name == "posix":
        null_device = "/dev/null"
    else:
        logging.error("This platform is not supported! [%s]" % os.name)
        sys.exit(1)
    if os.system('"' + java_path + '"' + ' -version >' + null_device + ' 2>' + null_device) != 0:
        logging.error("The specified java is not available! [%s]" % java_path)
        sys.exit(1)
    # 检查Grinder是否可用
    grinder_home = os.path.abspath(grinder_home)
    if not os.path.exists(grinder_home + os.sep + "lib" + os.sep + "grinder.jar"):
        logging.error("No such directory! [%s]" % grinder_home)
        sys.exit(1)
    # grinder_properties_file需要转换为绝对路径
    grinder_properties_file = os.path.abspath(grinder_properties_file)
    if not os.path.exists(grinder_properties_file):
        logging.error("No such file! [script_file=%s]" % grinder_properties_file)
        return
    # 构造CLASSPATH
    classpath = '"' + os.sep.join([grinder_home, "lib", "*"]) + '"'
    # 构造命令并执行
    if os.name == "nt":
        cmd = 'call ' + java_path + ' -classpath ' + classpath + ' net.grinder.Grinder ' + grinder_properties_file
    elif os.name == "posix":
        cmd = java_path + ' -classpath ' + classpath + ' net.grinder.Grinder ' + grinder_properties_file
    else:
        logging.error("This platform is not supported! [%s]" % os.name)
        sys.exit(1)
    logging.info("cmd: %s" % cmd)
    os.system(cmd)
    if os.path.exists(grinder_properties_file + ".bak"):
        os.remove(grinder_properties_file + ".bak")
    os.rename(grinder_properties_file, grinder_properties_file + ".bak")


def test():
    script_file = "scripts/java/call_java_method.py"
    script_file = "scripts/demo/helloworld.py"
    lib_directory = "scripts/java"
    generate_grinder_properties_file(script_file, lib_directory=lib_directory)
    run_testing()


if __name__ == "__main__":
    test()
    pass
