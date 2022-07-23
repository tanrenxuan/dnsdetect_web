detect_domain
检测DNS日志中请求域名是否异常（一条一判）
	- best_rf_clf.pkl：分类模型（该模型使用的是sklearn下的随机森林，已经训练好。在测试集上的准确率为94.476%）。
	- cdn_domain.txt：存放已知cdn后缀的文件，此后用于判断请求域名是否为cdn、waf的cname域名。
	- white_domain.txt：存放白名单域名的文件，存的都是二级域名（或内网的根域名）。
	- top-1m.tsv：该文件存放有2016年alexa网站统计的前100万排名，用于计算域名的特征（实际中只使用了前1000个域名，因此，若认为该文件过大，可自行保留前2000行即可）
	- word_frequency.txt：高频单词，用来计算域名的特征。
	- state_matrix.npy：字母转移概率矩阵，用来计算域名的特征
	- detect.py：检测文件

调用方式：
	初始化对象：
	d = DetectDomain(ignore_low=False)
	ignore_low: 若为True，表示忽略cdn域名告警，则不会显示cdn域名告警；若为False，则显示cdn域名告警
	d.detect(domain, client_ip, timestamp)
		:param domain: DNS日志requestDomain字段
       		:param client_ip: DNS日志clientIp字段
        		:param timestamp: DNS日志startTimeNs字段
	告警格式：[clientIp, requestDomain, startTineNs, level, 异常类型， 具体信息]
		e.g. ['1.2.3.4', 'www.sdasdjkk.com', 1650606260750654143, 'high', '域名异常', '该域名可能是dga动态生成域名，判定概率较高']


detect_behavior:
检测DNS日志中当前时间段每一个IP的行为是否符合历史同期。（一段时间判断一次，但数据输入是来一条调用一次detect）
	history_dict.pkl：存放所有ip历史数据
	collect.py：收集模块，用来收集当前时间段的数据。
	detect.py：检测模块，设置定时任务检测。
	dns_utils.py：一些工具函数。
调用方式：
CollectBehavior
	初始化：c = CollectBehavior()
	调用：c.collect( startTimeNs: int, clientIp: str, errorInfo: int, clientPort: int, requestDomain: str)
		        :param startTimeNs: DNS日志字段
		        :param clientIp: DNS日志字段
		        :param errorInfo: DNS日志字段
		        :param clientPort: DNS日志字段
		        :param requestDomain: DNS日志字段
	说明：该对象的collect方法是实时接收每一条数据的。redis虽然为单线程，但并发情况下，多个连接的命令仍然会出现数据不一致，所以增加了事务操作，确保统计无误。
		collect对外部的检测是无感知能力的，它无法感知此刻在哪一个时间段。
DetectBehavior:
	初始化：d = DetectBehavior(gate=False, collect=True, method='rule', data_path='history_dict.pkl)
	gate：若为True，则同时检测该时间段内是否出现未曾出现的ip、每一个ip是否访问了未曾访问的域名；若为False，则不检测。（系统运行一段时间后再开启，否则误报很多）
	collect：若为True，表示收集状态，不检测，只收集数据。  若为False，表示检测状态，检测并收集数据。
	method：'rule'表示基于规则， 'outlier'表示基于异常点检测算法（孤立森林）
	data_path：历史行为数据路径

	测试时，可以先使用d = DetectBehavior(gate=False, collect=True)收集一段时间。
		有了一定数据后，再使用d = DetectBehavior(gate=False, collect=False)
	最后实际应用时，使用d = DetectBehavior(gate=True,collect=False)
		
	