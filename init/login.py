# -*- coding=utf-8 -*-
import copy
import time
from collections import OrderedDict
from time import sleep

from config.ticketConf import _get_yaml
from inter.GetPassCodeNewOrderAndLogin import getPassCodeNewOrderAndLogin1
from inter.GetRandCode import getRandCode
from inter.LoginAysnSuggest import loginAysnSuggest
from inter.LoginConf import loginConf
from myException.UserPasswordException import UserPasswordException


class GoLogin:
    def __init__(self, session, is_auto_code, auto_code_type):
        self.session = session
        self.randCode = ""
        self.is_auto_code = is_auto_code
        self.auto_code_type = auto_code_type

    # def auth(self):
    #     """
    #     认证
    #     :return:
    #     """
    #     authUrl = self.session.urls["auth"]
    #     authData = {"appid": "otn"}
    #     tk = self.session.httpClint.send(authUrl, authData)
    #     return tk

    def auth(self):
        """
        :return:
        """
        self.session.httpClint.send(self.session.urls["loginInitCdn1"])
        uamtkStaticUrl = self.session.urls["uamtk-static"]
        uamtkStaticData = {"appid": "otn"}
        return self.session.httpClint.send(uamtkStaticUrl, uamtkStaticData)

    def codeCheck(self):
        """
        验证码校验
        :return:
        """
        # codeCheck = self.session.urls["codeCheck"]
        # codeCheckData = {
        #     "answer": self.randCode,
        #     "rand": "sjrand",
        #     "login_site": "E"
        # }
        # fresult = self.session.httpClint.send(codeCheck, codeCheckData)
        codeCheckUrl = copy.deepcopy(self.session.urls["codeCheck1"])
        codeCheckUrl["req_url"] = codeCheckUrl["req_url"].format(self.randCode, int(time.time() * 1000))
        fresult = self.session.httpClint.send(codeCheckUrl)
        if not isinstance(fresult, dict):
            fresult = eval(fresult.split("(")[1].split(")")[0])
        if "result_code" in fresult and fresult["result_code"] == "4":
            print(u"验证码通过,开始登录..")
            return True
        else:
            if "result_message" in fresult:
                print(fresult["result_message"])
            sleep(1)
            self.session.httpClint.del_cookies()

    def baseLogin(self, user, passwd):
        """
        登录过程
        :param user:
        :param passwd:
        :return: 权限校验码
        """
        logurl = self.session.urls["login"]

        loginData = OrderedDict()
        loginData["username"] = user,
        loginData["password"] = passwd,
        loginData["appid"] = "otn",
        loginData["answer"] = self.randCode,

        tresult = self.session.httpClint.send(logurl, loginData)
        if 'result_code' in tresult and tresult["result_code"] == 0:
            print(u"登录成功")
            tk = self.auth()
            if "newapptk" in tk and tk["newapptk"]:
                return tk["newapptk"]
            else:
                return False
        elif 'result_message' in tresult and tresult['result_message']:
            messages = tresult['result_message']
            if messages.find(u"密码输入错误") is not -1:
                raise UserPasswordException("{0}".format(messages))
            else:
                print(u"登录失败: {0}".format(messages))
                print(u"尝试重新登陆")
                return False
        else:
            return False

    def getUserName(self, uamtk):
        """
        登录成功后,显示用户名
        :return:
        """
        if not uamtk:
            return u"权限校验码不能为空"
        else:
            uamauthclientUrl = self.session.urls["uamauthclient"]
            data = {"tk": uamtk}
            uamauthclientResult = self.session.httpClint.send(uamauthclientUrl, data)
            if uamauthclientResult:
                if "result_code" in uamauthclientResult and uamauthclientResult["result_code"] == 0:
                    print(u"欢迎 {} 登录".format(uamauthclientResult["username"]))
                    return True
                else:
                    return False
            else:
                self.session.httpClint.send(uamauthclientUrl, data)
                url = self.session.urls["getUserInfo"]
                self.session.httpClint.send(url)

    def go_login(self):
        """
        登陆
        :param user: 账户名
        :param passwd: 密码
        :return:
        """
        user, passwd = _get_yaml()["set"]["12306account"][0]["user"], _get_yaml()["set"]["12306account"][1]["pwd"]
        if not user or not passwd:
            raise UserPasswordException(u"温馨提示: 用户名或者密码为空，请仔细检查")
        login_num = 0
        while True:
            if loginConf(self.session):
                self.auth()

                devicesIdUrl = copy.deepcopy(self.session.urls["getDevicesId"])
                devicesIdUrl["req_url"] = devicesIdUrl["req_url"].format(int(time.time() * 1000))
                # devicesIdRsp = self.session.httpClint.send(devicesIdUrl)
                # devicesId = eval(devicesIdRsp.split("(")[1].split(")")[0].replace("'", ""))["dfp"]
                devicesId = "UysLb2cYwsVjyInSzZ0pGOmYplvokmhBjoGNjrinquaUD0id7gkifgF6FvM2TRCL7Df89GZL1lVV763tGhiPhxlNdlE7iQkk496KUGCFZyyWxE4d0XjyHYv9DlsXfKTlrd8RBUdYIYjmWBXWMN65ElDQiO_Rnrul"

                if devicesId:
                    self.session.httpClint.set_cookies(RAIL_DEVICEID=devicesId)

                result = getPassCodeNewOrderAndLogin1(session=self.session, imgType="login")
                if not result:
                    continue
                self.randCode = getRandCode(self.is_auto_code, self.auto_code_type, result)
                print(self.randCode)
                login_num += 1
                self.auth()
                if self.codeCheck():
                    uamtk = self.baseLogin(user, passwd)
                    if uamtk:
                        self.getUserName(uamtk)
                        break
            else:
                loginAysnSuggest(self.session, username=user, password=passwd)
                login_num += 1
                break
