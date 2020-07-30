# -*- encoding: utf-8 -*-
"""
@File    : weread_automation.py
@Time    : 2020/7/1 14:22
@Author  : panziqiang007
@Email   : panziqiang007@qq.com
@Software: PyCharm
微信读书PC端 时长
chrome-version 84.0.4147.89
"""
import datetime
import json
import logging
import os
import re
from logging.handlers import RotatingFileHandler

import requests
import selenium.webdriver.support.expected_conditions as EC
import random
import time
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait


class log_v2(logging.Logger):

    def __init__(self, name='Server', level='INFO', file='logs.log', encoding='utf-8'):
        super().__init__(name)  # Logger(name)
        # 级别
        self.setLevel(level)
        # 格式
        fmt = '%(asctime)s - %(levelname)s : %(message)s'
        ft = logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')
        # 初始化输出渠道
        file_handle = RotatingFileHandler(file, encoding=encoding, maxBytes=1024 * 1024 * 10, backupCount=10)
        file_handle.setLevel(level)
        file_handle.setFormatter(ft)
        self.addHandler(file_handle)
        # 设置handle2
        h2 = logging.StreamHandler()
        h2.setFormatter(ft)
        # 将handle添加到logger
        self.addHandler(h2)


class DingTalk():

    def __init__(self):
        log_name = 'dingtalk.log'
        self.log = log_v2(file=log_name)

    def send_msg(self, content):
        textmod = {
            "msgtype": "markdown",
            "markdown": {
                "title": "监控报警",
                "text": content},  # markdown格式的消息
            "at": {
                "atMobiles": [
                    "13800000000"  # 被@人的手机号（在text内容里要有@手机号）
                ],
                "isAtAll": False  # 是否@所有人
            }
        }
        textmod = json.dumps(textmod)
        header_dict = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
            "Content-Type": "application/json"}
        url = '你自己的钉钉回调url地址'
        res = requests.post(url=url, data=textmod, headers=header_dict)
        res = res.json()
        if res['errmsg'] == "ok":
            self.log.info('success send')
        else:
            self.log.info(f'fail send:{res}')


class Selenium_():

    def __init__(self):
        """
        初始化 chrome 浏览器相关
        """
        # 参数
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        # chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])  # 开发者模式
        chrome_options.add_experimental_option("useAutomationExtension", False)  # 关闭 禁用开发者 的提示

        # 初始化 selenium 类
        self.driver = webdriver.Chrome(options=chrome_options, executable_path='chromedriver')
        self.wait = WebDriverWait(self.driver, 10, 0.5)
        self.ac = ActionChains(self.driver)

        # 针对80版本以上的chrome修改webdriver属性
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
          """
        })

        self.log_name = 'weread.log'
        self.log = log_v2(file=self.log_name)
        self.ding = DingTalk()

    def get_now_time(self):
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def slow_input(self, ele, word):
        for i in word:
            # 输出一个字符
            ele.send_keys(i)
            # 随机睡眠0.2到0.2秒
            sleep(random.uniform(0.2, 0.4))

    def wait_xpath(self, xpath_):
        """
        等待 xpath 元素
        :param xpath:
        :return:
        """
        return self.wait.until(EC.presence_of_element_located((By.XPATH, xpath_)))

    def wait_id(self, id_):
        """
        等待 id 元素
        :param id_:
        :return:
        """
        return self.wait.until(EC.presence_of_element_located((By.ID, id_)))

    def wait_classname(self, classname_):
        """
        等待 classname 元素
        :param wait_classname:
        :return:
        """
        return self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, classname_)))

    def close_sm(self):
        return self.driver.close()

    def sleep_time(self, hour, min, sec=60):
        # 定时器
        timer = hour * 3600 + min * 60 + sec
        return timer

    def get_read_time(self, read_time=0):
        read_time = int(read_time) + 1

        message = f"{'*' * 20} 启动读书程序 {'*' * 20}"
        self.log.info(message)

        second = self.sleep_time(0, 0, 60)
        min = 0
        while True:
            time.sleep(second)

            js = 'window.scrollBy(0,-100)'
            self.driver.execute_script(js)
            js = 'window.scrollBy(0,100)'
            self.driver.execute_script(js)

            min += 1
            content = f"本次读书 {min} 分钟"
            content_1 = f"累积读书 {min + read_time} 分钟"

            m = min + read_time
            h, m = divmod(m, 60)
            h = "%02d" % h
            m = "%02d" % m
            content_2 = f"累积读书 {h}小时 {m}分钟"

            self.log.info(content)
            self.log.info(content_1)
            self.log.info(content_2)
            self.ding.send_msg(content_2)


def get_file_data():
    file = 'weread.log'
    data_list = []

    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            for data in f:
                # print(data)
                res = re.findall(r"累积读书 (\d+) 分钟", data)
                if res:
                    # print(res[0])
                    data_list.append(res[0])

            if data_list:
                # print(data_list[-1])
                return data_list[-1]
            else:
                data_list.append(0)
                return data_list[-1]
    else:
        pass


if __name__ == '__main__':
    dd = DingTalk()
    try:
        content = "#### @1380000000 \n 开始读书啦！"
        dd.send_msg(content)
        res = get_file_data()
        sm = Selenium_()
        url = 'https://weread.qq.com/web/reader/efc326105dd846efcc90f7bk65132ca01b6512bd43d90e3'
        sm.driver.get(url)
        # sm.log.info(f"开始读书：{sm.get_now_time()}")
        sm.get_read_time(res)
        # sm.log.info(f"结束读书：{sm.get_now_time()}")
        # sleep(300000)
    except Exception as e:
        content = "#### @1380000000 \n 程序挂掉啦！"
        dd.send_msg(content)
