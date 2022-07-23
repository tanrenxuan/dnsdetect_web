from typing import Union

import requests


class AlartCrud:
    def __init__(self, base_url='http://10.209.44.150:8000/dns'):
        self.base_url = base_url

    def query_by_ip(self, ip: str) -> list:
        url = self.base_url + '/ip'
        response_list = requests.get(url, params={'ip': ip}).json()
        return response_list

    def query_by_domain(self, domain: str) -> list:
        url = self.base_url + '/domain'
        response_list = requests.get(url, params={'domain': domain}).json()
        return response_list

    def query_all(self) -> list:
        url = self.base_url + '/all'
        response_list = requests.get(url).json()
        return response_list

    def detect_and_insert(self, client_ip: str, domain: str, access_time: Union[str, int]) -> Union[dict, None]:
        url = self.base_url + '/'
        alart = {
            'client_ip': client_ip,
            'domain': domain,
            'access_time': access_time
        }
        response = requests.post(url, json=alart).json()
        return response

    def detect_and_insert_files(self, file):
        url = self.base_url + '/file'
        file_para = {'file': file}
        response_list = requests.post(url, files=file_para).json()
        return response_list


if __name__ == '__main__':
    # 初始化查询对象，'http://10.209.44.150:8000/dns'
    a = AlartCrud('http://127.0.0.1:8000/dns')

    # 查询所有的告警
    all_list = a.query_all()

    # 根据某ip查询告警
    certain_ip_list = a.query_by_ip('1.2.3.5')

    # 根据域名查询告警
    certain_domain_list = a.query_by_domain('newtab.firefoxchina.cn.wscdns.com')

    # 检测一条日志，若检测结果为异常则存入数据库，并返回该告警
    detect_alart = a.detect_and_insert(access_time=1234567845, client_ip='5.4.3.2', domain='www.baidu.com')

    # 传入json文件，必须含有client_ip、domain、access_time三个字段
    file = open('dns-1day.json', 'rb')
    print(a.detect_and_insert_files(file))
