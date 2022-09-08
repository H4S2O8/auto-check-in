# -*- coding:utf-8 -*-
from datetime import datetime, timedelta, timezone
import random
import sys

import requests
from requests import Session

from mycqu.auth import login_sso


def get_time_str():
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
    return bj_dt.strftime("%Y-%m-%d %H:%M:%S")


def log(content):
    print(get_time_str() + ' ' + str(content))
    sys.stdout.flush()


class InfoException(Exception):
    """信息异常"""

    def __init__(self, info):
        log(info)


class Check:
    def __init__(self, username: str, password: str, server_chan_subscription_key: str):
        self.session = Session()
        self.username = username
        self.password = password
        self.result = ""
        self.info = ""
        self.server_chan_subscription_key = server_chan_subscription_key

    def login(self):
        login_sso(session= self.session,
                  username= self.username,
                  password= self.password,
                  timeout= 50)

    def get_cookies(self):
        self.session.post(
            url="http://i.cqu.edu.cn/qljfwapp4/sys/lwStuReportEpidemic/modules/healthClock/T_HEALTH_DAILY_INFO_SAVE.do",
            allow_redirects=True)
        self.session.get(url="http://i.cqu.edu.cn/login?service=http://i.cqu.edu.cn/new/index.html",
                         allow_redirects=True)
        self.session.get(url="http://i.cqu.edu.cn/jsonp/appIntroduction.json?appId=6472205388186120&_=1661534633446",
                         allow_redirects=True)
        self.session.get("http://i.cqu.edu.cn/qljfwapp4/sys/lwStuReportEpidemic/index.do#/healthClock",
                         allow_redirects=True)

    def get_wid(self) -> str:
        resp = self.session.post(
            url="http://i.cqu.edu.cn/qljfwapp4/sys/lwStuReportEpidemic/modules/healthClock/getMyTodayReportWid.do")

        wid: str = ""
        try:
            wid = resp.json()['datas']['getMyTodayReportWid']['rows'][0]['WID']
        except IndexError:
            self.info = "获取wid失败"
            raise InfoException(self.info)
        return wid

    def get_data(self, wid: str) -> dict:
        resp = self.session.post(
            "http://i.cqu.edu.cn/qljfwapp4/sys/lwStuReportEpidemic/modules/healthClock/getMyDailyReportDatas.do?pageNumber=1&pageSize=10")
        try:
            data = resp.json()['datas']['getMyDailyReportDatas']['rows'][0]
        except IndexError:
            self.info = "获取旧数据失败"
            raise InfoException(self.info)

        t = datetime.now()
        if t.hour >= 11:
            t = t.replace(hour=random.randint(7, 10))
        date1 = t.strftime("%Y-%m-%d")
        czrq = t.strftime("%Y-%m-%d %H:%M:%S")
        created_at = t + timedelta(seconds=-1)
        created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
        fill_time = t + timedelta(minutes=-2, seconds=random.randint(-59, -1))
        fill_time = fill_time.strftime('%Y-%m-%d %H:%M:%S')

        data['WID'] = wid

        data['CZRQ'] = czrq
        data['CREATED_AT'] = created_at
        data['FILL_TIME'] = fill_time
        data['NEED_CHECKIN_DATE'] = date1

        data["CHECKED"] = None
        data["CHECKED_DISPLAY"] = None
        data["XQ"] = '004'
        data["XQ_DISPLAY"] = '虎溪校区'
        data["DZ_DKWZ"] = 6
        data["DZ_DKWZ_DISPLAY"] = '虎溪校内'

        return data

    def checkin(self, data: dict) -> dict:
        resp = self.session.post(
            "http://i.cqu.edu.cn/qljfwapp4/sys/lwStuReportEpidemic/modules/healthClock/T_HEALTH_DAILY_INFO_SAVE.do",
            params=data)
        print(resp.text)
        return resp.json()

    def confirm(self):
        data = {}
        resp = self.session.post(
            "http://i.cqu.edu.cn/qljfwapp4/sys/lwStuReportEpidemic/modules/healthClock/getMyDailyReportDatas.do?pageNumber=1&pageSize=10")
        try:
            data = resp.json()['datas']['getMyDailyReportDatas']['rows'][0]
        except IndexError:
            self.info = "获取旧数据失败"
            raise InfoException(self.info)
        date = data['NEED_CHECKIN_DATE']
        t = datetime.now()
        date1 = t.strftime("%Y-%m-%d")
        if date == date1:
            pass
        else:
            self.info = "出现错误，今日打卡失败！"
            raise InfoException(self.info)

    def main(self):
        wid = ""
        data = {}
        try:
            self.login()
            self.get_cookies()
            wid = self.get_wid()
            data = self.get_data(wid)
        except InfoException as e:
            self.result = "打卡失败"
            log(e)
        else:
            try:
                self.checkin(data)
                self.confirm()
            except InfoException as e:
                self.result = "打卡验证失败"
                log(e)
            else:
                self.result = '成功'
                self.info = '今日打卡成功'
                t = datetime.now()
                log(t.strftime('%m-%d') + '打卡成功')
        finally:
            requests.post(url=f"https://sctapi.ftqq.com/{self.server_chan_subscription_key}.send",
                          data={"text": self.result, "desp": self.info})

if __name__ == '__main__':
    user_name = sys.argv[1]
    password = sys.argv[2]
    server_chan_subscription_key = sys.argv[3]

    check =Check(user_name, password, server_chan_subscription_key)
    check.main()
