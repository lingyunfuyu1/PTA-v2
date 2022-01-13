#!/usr/bin/python
# coding:utf-8

"""
Created on 2016年11月23日

@author: hzcaojianglong
"""
import logging
import os
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import time


def mail(receiver_list, subject, content, image_list=[], attachment_list=[], sender="pta_system@pta.server.org", _subtype="html"):
    """
    发送带附件的邮件
    :param receiver_list: 收件人列表，列表格式
    :param subject: 邮件主题，字符串格式
    :param content: 邮件正文内容，字符串格式
    :param image_list: 邮件图片列表，列表格式，可以传多个图片，每个图片需包含路径，避免open的时候找不到
    :param attachment_list: 邮件附件列表，列表格式，可以传多个附件，每个附件需包含路径，避免open的时候找不到
    :param sender: 发件人，字符串格式，可不传，不传默认system
    :param _subtype: 邮件正文内容类型，字符串格式，可不传，不传默认plain
    :return:
    """
    mail_host = "smtp.163.com"
    mail_user = "testcaojl@163.com"
    mail_pass = "mail password"

    message = MIMEMultipart("related")
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = ",".join(receiver_list)

    for i in range(len(image_list)):
        image = image_list[i]
        fp = open(image, 'rb')
        message_image = MIMEImage(fp.read())
        fp.close()
        image_name = os.path.splitext(os.path.basename(image))[0] + str(i)
        message_image.add_header('Content-ID', "<image-" + image_name + ">")
        message.attach(message_image)
        content = content + '<img src="cid:image-' + image_name + '">'
    message.attach(MIMEText(content, _subtype, 'utf-8'))
    for attachment in attachment_list:
        attach = MIMEText(open(attachment, 'rb').read(), 'base64', 'utf-8')
        attach["Content-Type"] = 'application/octet-stream'
        attach["Content-Disposition"] = 'attachment; filename=' + os.path.basename(attachment)
        message.attach(attach)
    while True:
        try:
            smtp_object = smtplib.SMTP()
            smtp_object.connect(mail_host, 25)
            smtp_object.login(mail_user, mail_pass)
            smtp_object.sendmail(mail_user, receiver_list, message.as_string())
            smtp_object.quit()
            break
        except smtplib.SMTPException, e:
            logging.exception("Exception occurred when sending a mail!")
            time.sleep(900)


def test():
    result_directory = "result"
    mode = "test"
    testcase_dirname = "helloworld-20170315134401"
    work_directory = os.sep.join([result_directory, mode, testcase_dirname])
    # #######发送邮件#######
    mail_receiver_list = ["caojl01@gmail.com", "hzcaojianglong@corp.netease.com"]
    mail_subject = u"性能测试自动化执行报告"
    # 邮件正文
    content = open(os.sep.join([work_directory, "report.html"])).read()
    # 发送邮件
    logging.info("Sending email to %s" % str(mail_receiver_list))
    mail(mail_receiver_list, mail_subject, content)


if __name__ == "__main__":
    test()
    pass
