"""
与网络请求相关的模块
"""

import json
import httpx
from dataclasses import field, dataclass
from typing import Any, Dict, Union

# from ..log import logger
from app.exceptions import ApiException, ResponseCodeException
from app.config.mcim import MCIMConfig

mcim_config = MCIMConfig.load()


PROXY: str = mcim_config.proxies

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.54",
}

TIMEOUT = 5
RETRY_TIMES = 3
REQUEST_LOG = True

def retry(times: int = RETRY_TIMES):
    """
    重试装饰器

    Args:
        times (int): 最大重试次数 默认 3 次 负数则一直重试直到成功

    Returns:
        Any: 原函数调用结果
    """

    def wrapper(func):
        def inner(*args, **kwargs):
            nonlocal times
            loop = times
            while loop != 0:
                loop -= 1
                try:
                    return func(*args, **kwargs)
                except json.decoder.JSONDecodeError:
                    continue
                except ResponseCodeException as e:
                    raise e
                # TIMEOUT
            raise ApiException("重试达到最大次数")

        return inner

    return wrapper

@retry()
def request(url: str, method: str = "GET", data=None, params=None, json=None, **kwargs) -> httpx.Response:
    """
    HTTPX 请求函数

    Args:
        url (str): 请求 URL

        method (str, optional): 请求方法 默认 GET

        **kwargs: 其他参数

    Returns:
        Any: 请求结果
    """
    if json is not None:
        res = httpx.request(method, url, proxies=PROXY, json=json, params=params, **kwargs)
    else:
        res = httpx.request(method, url, proxies=PROXY, data=data, params=params, **kwargs)
    if res.status_code != 200:
        raise ResponseCodeException(status_code=res.status_code, method=method, url=url, data=data if data is None else json, params=params, msg=res.text)
    return res