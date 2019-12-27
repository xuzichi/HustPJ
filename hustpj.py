import requests
from lxml import etree
from lxml import html
import execjs
import re

username = ''  # 在这里输入自己的学号
password = ''  # 在这里输入自己的密码
xnxq = '20191'
pjlc = '2019101'
login = 'https://pass.hust.edu.cn/cas/login?service=http%3A%2F%2Fcurriculum.hust.edu.cn%2Fhustpass.do'

# 使用会话保持 cookie
s = requests.Session()

# 首次请求，获取隐藏参数
start_response = s.get(login)
start_html = etree.HTML(start_response.text, parser=etree.HTMLParser())
lt = start_html.xpath('//*[@id="fm1"]/input[6]/@value')[0]
execution = start_html.xpath('//*[@id="fm1"]/input[7]/@value')[0]
_eventId = start_html.xpath('//*[@id="fm1"]/input[8]/@value')[0]
# 调用 JavaScript 对密码加密
with open('login.js', 'r') as f:
    js_login = f.read()

ctx = execjs.compile(js_login)
username_result = ctx.call('encryptedString', username)
password_result = ctx.call('encryptedString', password)
print(username_result)
print(password_result)

# 登录
data = {
    'username': username_result,
    'password': password_result,
    'lt': lt,
    'execution': execution,
    '_eventId': _eventId,
}
login_response = s.post(login, data=data)  # 重定向请求必须加上 allow_redirects=False

url = 'http://curriculum.hust.edu.cn/cc_HustWspjTeacherAction.do'
for page in [1, 2, 3]:
    # 进入评教主界面获取课程代码kcdm、老师人数size以及初始的jsid（根据num改变的，初始的便是num=0时的）
    data_1 = {
        'hidOption': 'getWspjPjlc',
        'page': page,
        'xnxq': 'null',
        'userid': username
    }
    data_2 = {
        'hidOption': 'getWspjToKC',
        'userid': username,
        'page': page,
        'xnxq': xnxq,
        'pjlc': pjlc,
    }
    response = s.post(url, data=data_1)
    response = s.post(url, data=data_2)
    html_page = html.fromstring(response.text)
    result = html_page.xpath('//div[contains(@style, "cursor:pointer;")]/@onclick')
    kcdm = []
    for result_i in result:
        if re.match('^gotoKcpj\(\'\',\'(\w*)', result_i) is None:
            if re.match('^gotoWspj\(\'\',\'(\w*)', result_i) is None:
                pass
            else:
                kcdm.append(re.match('^gotoWspj\(\'\',\'(\w*)', result_i).group(1))
        else:
            kcdm.append(re.match('^gotoKcpj\(\'\',\'(\w*)', result_i).group(1))
    html_page = html.fromstring(response.text)
    size = html_page.xpath('//input[@name="size"]/@value')

    # 开始评教
    url_submit = 'http://curriculum.hust.edu.cn/cc_HustWspjTeacherAction.do?hidOption=SAVE'
    for kcdm_i in kcdm:
        print(kcdm_i)
        url_size = 'http://curriculum.hust.edu.cn/wspj/awspj.jsp'
        querystring = {
            'kcdm': kcdm_i,  # 课程代码
            'xnxq': '20191',
            'pjlc': '2019101',
            'num': '0',
        }
        response = s.get(url_size, params=querystring)
        page = html.fromstring(response.text)
        size = page.xpath('//input[@name="size"]/@value')
        size = int(size[0])
        for num in range(size):
            querystring = {
                'kcdm': kcdm_i,  # 课程代码
                'xnxq': '20191',
                'pjlc': '2019101',
                'num': num,
            }
            response = s.get(url_size, params=querystring)
            page = html.fromstring(response.text)
            jsid = page.xpath('//input[@name="jsid"]/@value')
            jsid = jsid[0]
            data = {
                'hidOption': 'ADD',
                'hidKey': '',
                'commit': '0001,95,01@0002,95,01@0003,95,01@0004,95,01@0005,95,01@0006,95,01@',
                'id': '',
                'size': size,  # 老师的总数量
                'num': num,  # 老师的代号
                'zbmb': '008',
                'pjlx': '01',
                'jsid': jsid,
                'kcdm': kcdm_i,  # 课程代码
                'xnxq': '20191',
                'pjlc': '2019101',
                'userid': username,
                'grade0': '95',
                'grade1': '95',
                'grade2': '95',
                'grade3': '95',
                'grade4': '95',
                'grade5': '95',
                'yjjy': '',
                'yp_flag': '0',
            }
            response = s.post(url_submit, data=data)
            print(response.text)
            print(kcdm_i + '课程的第' + str(num) + '老师已完成')
        print(kcdm_i + '课程已完成')
