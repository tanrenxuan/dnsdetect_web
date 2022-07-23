# dnsdetect_web

向外提供了5种api接口，可以满足基本的检测与查询操作。

服务所在主机ip与端口：http://10.209.44.150:8000

## 检测dns日志

该部分接口用于检测日志，若模型判断为异常，则将详细告警信息存入数据库中。

- http://10.209.44.150:8000/dns/

  该接口为`post`请求，参数结构

  ```python
  {
      'client_ip': '12.34.56.78',
      'domain': 'www.sjjdnehsask.cn',
      'access_time': '4556345671'
  }
  ```

  *注：client_ip指的是发起DNS查询的源ip，domain指的是查询的域名（也是算法检测的部分）， access_time指的是时间戳，至少到秒级别，毫秒或纳秒级别也可以。*

  若模型判断正常，则返回None；否则，返回结构如下：

  ```python
  {
    "client_ip": "12.34.56.78",
    "domain": "www.sjjdnehsask.cn",
    "access_time": "2114-05-21T19:34:31",
    "warn_info": "该域名可能是dga动态生成域名，判定概率较高",
    "warn_level": "high",
    "warn_time": "2022-07-23T19:29:31"
  }
  ```

- http://10.209.44.150:8000/dns/file

  该接口也为post请求，由于第一个接口只能一次检测一个域名，该接口支持上传json文件。**json文件的要求：必须包含access_time、domain和client_ip三个字段。**

  返回的是告警事件列表，即上传文件中被检测为异常的日志对应的告警（若全部正常，则返回空列表）

  ```python
  [
    {
      "client_ip": "22.12.0.3",
      "domain": "newtab.firefoxchina.cn.wscdns.com",
      "access_time": "2022-04-22T13:44:19",
      "warn_info": "该域名属于cname，可能使用了cdn、waf",
      "warn_level": "mid",
      "warn_time": "2022-07-23T19:54:26"
    },
    {
      "client_ip": "30.18.139.237",
      "domain": "dns.msftncsi.com",
      "access_time": "2022-04-22T13:44:19",
      "warn_info": "该域名可能是dga动态生成域名，判定概率较低",
      "warn_level": "mid",
      "warn_time": "2022-07-23T19:54:26"
    },
      
      ...
      
    {
      "client_ip": "22.12.0.3",
      "domain": "toblog.ctobsnssdk.com",
      "access_time": "2022-04-22T13:44:22",
      "warn_info": "该域名可能是dga动态生成域名，判定概率较高",
      "warn_level": "high",
      "warn_time": "2022-07-23T19:54:26"
    }
  ]
  ```

## 查询接口

该部分接口用于查询已有的告警，均为get请求。可以分别根据ip、domain查询，也可以查询现有所有告警。返回的均是告警事件列表，与http://10.209.44.150:8000/dns/file的返回结构类似，这里不再赘述。

- http://10.209.44.150:8000/dns/ip
- http://10.209.44.150:8000/dns/domain
- http://10.209.44.150:8000/dns/all

## 说明

文件example.py提供了简单的基于`python`的`requests`模块访问的例子。更详细的api接口文档可参考`http://10.209.44.150:8000/docs`