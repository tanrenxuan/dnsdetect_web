import warnings
import csv
import time
import datetime
import joblib
import numpy as np
import pandas as pd
import redis
import tldextract
import pytz
from math import log2

warnings.filterwarnings('ignore')


class GetDomainFeature:

    def __init__(self, jaccard_n=1000, log_flag: bool = False):
        self.valid_domain_list = self.get_valid_domain(top=jaccard_n)['domain'].to_list()  # 作为计算平均jaccard指数的合法域名
        self.curr_num = 0
        self.readability = 0.018782  # 论文中的设置
        self.state_matrix = self.init_state_matrix()
        self.most_words = self.init_most_words()
        self.log_flag = log_flag

    def get_valid_domain(self, filepath: str = 'detect_util/top-1m.csv', top: int = 100000):
        valid_domain_set = set()
        with open(filepath) as f:
            f_reader = csv.reader(f)
            for row in f_reader:
                domain = tldextract.extract(row[1])[1]  # (subdomain, domain, suffix)
                if domain == '':  # 域名本身就是后缀
                    continue
                valid_domain_set.add(domain)
                if len(valid_domain_set) >= top:
                    break
        return pd.DataFrame(valid_domain_set, columns=['domain'])

    def init_state_matrix(self):
        file_name = 'detect_util/state_matrix.npy'
        return np.load(file_name, allow_pickle=True).item()  # 加载字符转移矩阵

    def init_most_words(self):
        file_name = 'detect_util/word_frequency.txt'
        with open(file_name, 'r', encoding='ISO-8859-1') as f:
            f.readline()  # 略去开头
            word_set = set()
            for line in f:
                word = line.split()[0]
                if word.isalpha():  # 有一些含有*等
                    word_set.add(word.lower())
        return word_set

    @staticmethod
    def get_info_entropy(domain: str) -> float:
        """
        获取域名信息熵
        :param domain: 域名
        :return: 信息熵
        """
        char_dict = dict()
        for c in domain:
            char_dict[c] = 1 if c not in char_dict.keys() else char_dict[c] + 1
        entropy, length = 0, len(domain)
        for v in char_dict.values():
            probability = v / length
            entropy += probability * (-log2(probability))
        # return round(entropy, 1)
        return entropy

    def get_avg_jaccard(self, n: int = 2):
        """
        获取平均jaccard指数
        :param n: n相邻字符
        :param domain: 域名
        :return: 平均jaccard指数
        """

        def get_avg(domain: str):
            def get_n_chars_set(temp_domain: str):
                temp_set = set()
                for i in range(len(temp_domain) - 1):
                    temp_set.add(temp_domain[i:i + 2])
                return temp_set

            domain_set = get_n_chars_set(domain)

            def get_jaccard(valid_domain: str):
                valid_domain_set = get_n_chars_set(valid_domain)
                try:
                    jaccard = len(domain_set & valid_domain_set) / len(domain_set | valid_domain_set)
                    return jaccard
                except ZeroDivisionError:
                    return 1  # 说明都是单字符（n=2,3）或双字符（n=3），合法域名

            all_jaccard = 0
            for d in self.valid_domain_list:
                all_jaccard += get_jaccard(d)
            self.curr_num += 1
            if self.log_flag is True:
                print('complete [{:d}/200000]'.format(self.curr_num))
            return all_jaccard / len(self.valid_domain_list)

        return get_avg

    @staticmethod
    def get_length(domain: str) -> int:
        """
        获取域名长度L
        :param domain: 域名
        :return: 域名长度
        """
        return len(domain)

    @staticmethod
    def get_vowel_ratio(domain: str) -> float:
        """
        获取域名中元音字母占据总长度的比值S1
        :param domain: 域名
        :return: 比值
        """
        vowels = {'a', 'e', 'i', 'o', 'u'}  # 元音字母
        cnt = 0
        for c in domain:
            if c in vowels:
                cnt += 1
        return cnt / len(domain)

    @staticmethod
    def get_continue(domain: str, choice: str) -> float:
        """
        合并获取连续辅音和数字的逻辑
        :param domain: 域名
        :param choice: consonant 或 digit
        :return: 比例
        """
        assert choice in ['consonant', 'digit']

        def is_consonant(temp_c: str) -> bool:
            if temp_c.isalpha() and temp_c not in vowels:
                return True
            return False

        def is_digit(temp_c: str) -> bool:
            return temp_c.isdigit()

        if choice == 'consonant':
            is_func = is_consonant
        elif choice == 'digit':
            is_func = is_digit

        cnt = 0
        vowels = {'a', 'e', 'i', 'o', 'u'}  # 元音字母
        start_index = -1
        for index, c in enumerate(domain):
            if not is_func(c):
                continue_len = index - start_index - 1
                if continue_len >= 2:  # 连续辅音长度>=2
                    cnt += continue_len
                start_index = index
        continue_len = len(domain) - start_index - 1
        if continue_len >= 2:
            cnt += continue_len
        return cnt / len(domain)

    @staticmethod
    def get_continue_consonants_ratio(domain: str) -> float:
        """
        获取连续辅音字母总长度与域名总长度比例S2
        :param domain: 域名
        :return: 比值
        """
        return GetDomainFeature.get_continue(domain, choice='consonant')

    @staticmethod
    def get_digit_ratio(domain: str) -> float:
        """
        获取域名中数字比例S3
        :param domain: 域名
        :return: 比值
        """
        cnt = 0
        for c in domain:
            if c.isdigit():
                cnt += 1
        return cnt / len(domain)

    @staticmethod
    def get_continue_digit_ratio(domain: str) -> float:
        """
        获取连续数字比例S4
        :param domain: 域名
        :return: S4
        """
        return GetDomainFeature.get_continue(domain, choice='digit')

    @staticmethod
    def get_digit_alpha_change_ratio(domain: str):
        """
        获取字母和数字切换比例S5
        :param domain: 域名
        :return: S5
        """

        def is_change(two_chars: str) -> bool:
            a, b = two_chars[0], two_chars[1]
            if a.isdigit() and b.isalpha() or a.isalpha() and b.isdigit():
                return True
            return False

        cnt = 0
        for i in range(len(domain) - 1):
            if is_change(domain[i:i + 2]):
                cnt += 1
        return cnt / (len(domain) - 1) if (len(domain) - 1) > 0 else 0

    def get_readability(self, choice: int = 1):
        """
        获取域名可读性，采用闭包，函数对象参数化
        :param choice: 0表示离散化；1表示连续值
        :return: 若choice=0：0：不可读  1：可读；若choice=1：直接返回连续值
        """

        def readability(domain: str):
            ln_p = 0.0
            domain = domain.lower()
            for i in range(len(domain) - 1):
                if (domain[i].isalpha() and domain[i + 1].isalpha()) is False:
                    continue
                ln_p += self.state_matrix[domain[i]][domain[i + 1]]
            if choice == 1:
                return ln_p
            else:
                pass

        return readability

    def get_words_num_ratio(self, domain: str) -> float:
        """
        :param domain: 域名
        :return: 单词总数与域名长度比值W1
        """
        cnt = 0
        for l in range(2, len(domain) + 1):  # 2,3,...,L
            for start_index in range(len(domain) - l + 1):
                if domain[start_index:start_index + l] in self.most_words:
                    cnt += 1
        return cnt / len(domain)

    def get_words_len_ratio(self, domain: str):
        """
        :param domain: 域名
        :return: 单词总长度与域名长度比值W2
        """
        cnt = 0
        for l in range(2, len(domain) + 1):  # 2,3,...,L
            for start_index in range(len(domain) - l + 1):
                if domain[start_index:start_index + l] in self.most_words:
                    cnt += l  # 这里加单词长度
        return cnt / len(domain)


class WhiteList:
    """
    包括域名白名单、cdn域名集合
    """

    def __init__(self, cdn_path: str = 'detect_util/cdn_domain.txt',
                 white_path: str = 'detect_util/white_domain.txt'):
        # 读取cdn列表
        self._cdn_list = []
        with open(cdn_path, 'r', encoding='utf-8') as f:
            for cdn in f:
                self._cdn_list.append(cdn.replace('\n', ''))
        # 读取白名单列表
        self._white_list = set()
        with open(white_path, 'r', encoding='utf-8') as f:
            for white_domain in f:
                self._white_list.add(white_domain.replace('\n', ''))

    def get_cdn(self):
        return self._cdn_list

    def get_white(self):
        return self._white_list


class DetectDomain:
    def __init__(self, ignore_low: bool = False):
        self.redis_conn = redis.StrictRedis(host='localhost', port=6379, password=123456,
                                            db=2, decode_responses=True)
        self.curr_domains = 'curr_domains'  # 存放某时间段内已经检测到的告警域名
        self.feature_extract = GetDomainFeature()
        self.white_list = WhiteList()
        self.clf = joblib.load('detect_util/best_rf_clf.pkl')
        self.ignore_low = ignore_low  # 忽略cdn域名告警

    def _set_curr_domains(self):
        """
        设置12小时内已检测的告警域名集合
        """
        self.redis_conn.sadd(self.curr_domains, 1)  # 1用来占位
        self.redis_conn.expire(self.curr_domains, 12 * 60 * 60)  # 设置12小时过期的集合，保存12小时内检测异常的域名

    def _get_sld(self, origin_domain: str):
        """
        根据原始域名获取sld
        :param origin_domain: 原始域名
        :return:    bool：
                        若为False：表示过滤该域名不需检测
                        若为True：表示该域名为cname域名（cdn、waf等）
                        若为None：表示需要检测的正常sld
                    若有str：表示提取的待检测sld
        """
        if origin_domain.find('in-addr.arpa') != -1:  # 反向解析/DNS-SD不予考虑
            return False, None
        if tldextract.extract(origin_domain)[-1] == '':  # 没有该顶级域名，默认为企业内部域名
            return False, None
        for cdn in self.white_list.get_cdn():  # 属于cname域名
            if origin_domain.find(cdn) != -1:
                return True, cdn
        sld = tldextract.extract(origin_domain)[1].lower()
        for white_domain in self.white_list.get_white():
            if sld == white_domain:
                return False, None
        return None, sld

    def _filter(self, sld: str) -> bool:
        # 下面的更新操作在多线程情况下可能会重复更新，考虑到影响不大，可以不用互斥
        if not self.redis_conn.exists(self.curr_domains):  # 若过期，则重新设置
            self.redis_conn.sadd(self.curr_domains, sld)
            self.redis_conn.expire(self.curr_domains, 12 * 60 * 60)  # 设置12小时过期的集合，保存12小时内检测异常的域名
            return True  # 需要检测

        # 下面对域名进行判断是否在集合中必须互斥
        # 大多数重复域名出现在连续的日志中，如果不互斥，可能仍然会有许多重复域名
        pip = self.redis_conn.pipeline()
        pip.multi()
        pip.smembers(self.curr_domains)
        pip.sadd(self.curr_domains, sld)  # 重复插入相同元素不影响
        res = pip.execute()
        if sld not in res[0]:  # 不在该集合才进行检测
            return True  # 需要检测
        return False  # 不需要检测

    def detect(self, origin_log):
        """
        告警格式 [clientIp, requestDomain, startTineNs, level, 异常类型， 具体信息]
        :param domain: DNS日志requestDomain字段
        :param client_ip: DNS日志clientIp字段
        :param timestamp: DNS日志startTimeNs字段
        :return:
        """
        domain = origin_log["requestDomain"]
        client_ip = origin_log["clientIp"]
        timestamp = int(origin_log["startTimeNs"])
        now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        info_time = self.time2date(timestamp)
        status = "未处理"
        flag, sld = self._get_sld(domain)
        if flag is False:  # 过滤
            return None
        else:
            if not self._filter(sld):
                return None
            if flag is True:  # 警告，该域名属于cname
                if self.ignore_low is False:
                    warn_info = "该域名属于cname，可能使用了cdn、waf"
                    return {
                        'access_time': info_time,
                        'domain': domain,
                        'client_ip': client_ip,
                        'warn_info': warn_info,
                        'warn_level': 'mid',
                        'warn_time': now
                    }
            else:
                domain_vec = self._domain2vec(sld)
                score = self.clf.predict_proba(np.array(domain_vec.iloc[:, 1:]))[0][1]  # 去除domain字段
                if score > 0.5:  # 表示正常
                    if score > 0.9:
                        warn_info = "该域名可能是dga动态生成域名，判定概率较高"
                        return {
                            'access_time': info_time,
                            'domain': domain,
                            'client_ip': client_ip,
                            'warn_info': warn_info,
                            'warn_level': 'high',
                            'warn_time': now
                        }
                    else:
                        warn_info = "该域名可能是dga动态生成域名，判定概率较低"
                        return {
                            'access_time': info_time,
                            'domain': domain,
                            'client_ip': client_ip,
                            'warn_info': warn_info,
                            'warn_level': 'mid',
                            'warn_time': now
                        }
        return None

    def _domain2vec(self, domain: str) -> pd.DataFrame:
        """
        获取特征
        :param domain: 单个域名或域名dataframe
        :return: 获取特征后的dataframe
        """
        domain = pd.DataFrame([domain], columns=['domain'])
        func_dict = {  # 暂时有11个特征
            'info_entropy': self.feature_extract.get_info_entropy,
            'avg_jaccard': self.feature_extract.get_avg_jaccard(n=2),  # 2字符
            'readability': self.feature_extract.get_readability(1),  # 1连续值
            'length': self.feature_extract.get_length,
            'vowel_ratio': self.feature_extract.get_vowel_ratio,
            'continue_consonants_ratio': self.feature_extract.get_continue_consonants_ratio,
            # 'digit_ratio': self.feature_extract.get_digit_ratio,
            # 'continue_digit_ratio': self.feature_extract.get_continue_digit_ratio,
            # 'digit_alpha_change_ratio': self.feature_extract.get_digit_alpha_change_ratio,
            'words_num_ratio': self.feature_extract.get_words_num_ratio,
            'words_len_ratio': self.feature_extract.get_words_len_ratio
        }
        for key, value in func_dict.items():
            domain[key] = domain.apply(lambda x: value(x.domain), axis=1)
        return domain

    def time2date(self, timestamp: int):
        """
        时间戳转换为东八区时间
        :param timestamp: 时间戳(ns)
        :return: 东八区时间 (2018-04-12 02:03:40) 省去了毫秒
        """
        d = datetime.datetime.fromtimestamp(int(str(timestamp)[:10]), tz=pytz.timezone("Asia/Shanghai"))
        # 精确到秒
        str1 = d.strftime("%Y-%m-%d %H:%M:%S")
        return str1
