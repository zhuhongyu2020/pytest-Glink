#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2022-08-03 15:47:26
# @Author : 朱宏玉


import allure
import pytest
from common.setting import ConfigHandler
from utils.read_files_tools.get_yaml_data_analysis import CaseData
from utils.assertion.assert_control import Assert
from utils.requests_tool.request_control import RequestControl
from utils.read_files_tools.regular_control import regular
from utils.requests_tool.teardown_control import TearDownHandler


TestData = CaseData(ConfigHandler.data_path + r'Login/login.yaml').case_process()
re_data = regular(str(TestData))


@allure.epic("Glink平台")
@allure.feature("登录模块")
class TestLogin:

    @allure.story("登录")
    @pytest.mark.parametrize('in_data', eval(re_data), ids=[i['detail'] for i in TestData])
    def test_login(self, in_data, case_skip):
        """
        :param :
        :return:
        """
        res = RequestControl().http_request(in_data)
        TearDownHandler().teardown_handle(res)
        Assert(in_data['assert']).assert_equality(response_data=res['response_data'], 
                                                  sql_data=res['sql_data'], status_code=res['status_code'])


if __name__ == '__main__':
    pytest.main(['test_login.py', '-s', '-W', 'ignore:Module already imported:pytest.PytestWarning'])
