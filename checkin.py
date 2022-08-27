# -*- coding:utf-8 -*-
from datetime import datetime
from datetime import timedelta
import random

from requests import Session

from mycqu.auth import login_sso


s = Session()
login_sso(session=s,
          username='username',
          password='password')


resp = s.post(url="http://i.cqu.edu.cn/qljfwapp4/sys/lwStuReportEpidemic/modules/healthClock/T_HEALTH_DAILY_INFO_SAVE.do", allow_redirects=True)
s.get(url="http://i.cqu.edu.cn/login?service=http://i.cqu.edu.cn/new/index.html", allow_redirects=True)
s.get(url="http://i.cqu.edu.cn/jsonp/appIntroduction.json?appId=6472205388186120&_=1661534633446", allow_redirects=True)
s.get("http://i.cqu.edu.cn/qljfwapp4/sys/lwStuReportEpidemic/index.do#/healthClock", allow_redirects=True)

resp = s.post(url="http://i.cqu.edu.cn/qljfwapp4/sys/lwStuReportEpidemic/modules/healthClock/getMyTodayReportWid.do")
print(resp.text)
wid = resp.json()['datas']['getMyTodayReportWid']['rows'][0]['WID']


resp = s.post("http://i.cqu.edu.cn/qljfwapp4/sys/lwStuReportEpidemic/modules/healthClock/getMyDailyReportDatas.do?pageNumber=1&pageSize=10&WID=E70F6784DE40A8C1E05366D614AC20F3")
data = resp.json()['datas']['getMyDailyReportDatas']['rows'][0]

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


resp = s.post("http://i.cqu.edu.cn/qljfwapp4/sys/lwStuReportEpidemic/modules/healthClock/T_HEALTH_DAILY_INFO_SAVE.do",
              params=data)

print(resp.text)


