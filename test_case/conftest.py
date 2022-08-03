
import pytest
import time
import allure
import requests
from common.setting import ConfigHandler
from utils.read_files_tools.get_yaml_data_analysis import CaseData
from utils.cache_process.cache_control import Cache
from utils.read_files_tools.get_all_files_path import get_all_files
from utils.logging_tool.log_control import INFO, ERROR, WARNING
from Enums.yamlData_enum import YAMLDate
from utils.read_files_tools.clean_files import del_file
from utils.other_tools.allure_data.allure_tools import allure_step, allure_step_no

@pytest.fixture(scope="session", autouse=False)
def clear_report():
    """如clean命名无法删除报告，这里手动删除"""
    del_file(ConfigHandler.report_path)


@pytest.fixture(scope="session", autouse=True)
def write_case_process():
    """
    获取所有用例，写入用例池中
    :return:
    """

    case_data = {}
    # 循环拿到所有存放用例的文件路径
    for i in get_all_files(file_path=ConfigHandler.data_path, yaml_data_switch=True):
        # 循环读取文件中的数据
        case_process = CaseData(i).case_process(case_id_switch=True)
        if case_process is not None:
            # 转换数据类型
            for case in case_process:
                for k, v in case.items():
                    # 判断 case_id 是否已存在
                    case_id_exit = k in case_data.keys()
                    # 如果case_id 不存在，则将用例写入缓存池中
                    if case_id_exit is False:
                        case_data[k] = v
                    # 当 case_id 为 True 存在时，则跑出异常
                    elif case_id_exit is True:
                        raise ValueError(f"case_id: {k} 存在重复项, 请修改case_id\n"
                                         f"文件路径: {i}")
    Cache('case_process').set_caches(case_data)


@pytest.fixture(scope="session", autouse=True)
def work_login_init():
    """
    获取登录的cookie
    :return:
    """

    url = "https://lo9.glkyun.cn/sso/Account/LoginRedirect"
    data = "{\r\n    \"ReturnUrl\": \"/sso/connect/authorize/callback?client_id=lo_ptl_client&redirect_uri=https%3A%2F%2Flo9.glkyun.cn%2Fportal%2Foidc%2Fcallbackn.html&response_type=code&scope=openid%20profile%20lo_ptl%20lo_ofs%20lo_g_doc%20lo_gw&state=a63a5b41e89c48f7ae9a74f49c55a605&code_challenge=3Ye4G3L5Y6Eqv4CBscqnbT1kYw3wqE5wPIxP2PFV4QE&code_challenge_method=S256&response_mode=query\",\r\n    \"__RequestVerificationToken\": \"\",\r\n    \"LoginId\": \"liusj-e\",\r\n    \"LoginIdentity\": \"b0039003e003900280077002700770028007b006a00780078007c00640079006f\",\r\n    \"ImageAuthCode\": \"\",\r\n    \"RememberLogin\": \"true\"\r\n}"
    headers = {'Content-Type': 'application/json;charset=UTF-8'}
    # 请求登录接口

    res = requests.post(url=url, data=data, verify=True, headers=headers)
    response_cookie = res.cookies

    cookies = ''
    for k, v in response_cookie.items():
        _cookie = k + "=" + v + ";"
        # 拿到登录的cookie内容，cookie拿到的是字典类型，转换成对应的格式
        cookies += _cookie
        # 将登录接口中的cookie写入缓存中，其中login_cookie是缓存名称

    Cache('login_cookie').set_caches(cookies)


@pytest.fixture(scope="class")
def get_env(request):
    project_url = request.config.getoption("--project_url")
    return project_url


def pytest_collection_modifyitems(items):
    """
    测试用例收集完成时，将收集到的 item 的 name 和 node_id 的中文显示在控制台上
    :return:
    """
    for item in items:
        item.name = item.name.encode("utf-8").decode("unicode_escape")
        item._nodeid = item.nodeid.encode("utf-8").decode("unicode_escape")


# 定义单个标签
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "smoke"
    )


@pytest.fixture(scope="function", autouse=True)
def case_skip(in_data):
    """处理跳过用例"""
    if in_data['is_run'] is False:
        allure.dynamic.title(in_data[YAMLDate.DETAIL.value])
        allure_step_no(f"请求URL: {in_data[YAMLDate.IS_RUN.value]}")
        allure_step_no(f"请求方式: {in_data[YAMLDate.METHOD.value]}")
        allure_step("请求头: ", in_data[YAMLDate.HEADER.value])
        allure_step("请求数据: ", in_data[YAMLDate.DATA.value])
        allure_step("依赖数据: ", in_data[YAMLDate.DEPENDENCE_CASE_DATA.value])
        allure_step("预期数据: ", in_data[YAMLDate.ASSERT.value])
        pytest.skip()


def pytest_terminal_summary(terminalreporter):
    """
    收集测试结果
    """

    _PASSED = len([i for i in terminalreporter.stats.get('passed', []) if i.when != 'teardown'])
    _ERROR = len([i for i in terminalreporter.stats.get('error', []) if i.when != 'teardown'])
    _FAILED = len([i for i in terminalreporter.stats.get('failed', []) if i.when != 'teardown'])
    _SKIPPED = len([i for i in terminalreporter.stats.get('skipped', []) if i.when != 'teardown'])
    _TOTAL = terminalreporter._numcollected
    _TIMES = time.time() - terminalreporter._sessionstarttime
    INFO.logger.error(f"用例总数: {_TOTAL}")
    INFO.logger.error(f"异常用例数: {_ERROR}")
    ERROR.logger.error(f"失败用例数: {_FAILED}")
    WARNING.logger.warning(f"跳过用例数: {_SKIPPED}")
    INFO.logger.info("用例执行时长: %.2f" % _TIMES + " s")

    try:
        _RATE = _PASSED / _TOTAL * 100
        INFO.logger.info("用例成功率: %.2f" % _RATE + " %")
    except ZeroDivisionError:
        INFO.logger.info("用例成功率: 0.00 %")
