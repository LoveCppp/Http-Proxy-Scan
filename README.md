## Http-Proxy-Scan

利用censys.io快速更新全网的优势，爬取http代理。提取关键字为'Mikrotik','Squid','Proxy','Tinyproxy','Wingate','CCProxy','Pound'。如需添加请修改censys.io main函数的keyword字段，测试的端口号为8080、80、3128。


### 部署方法

* python 2.7.x
* mysql导入proxy.sql
* 修改dbconnect.py数据库连接信息
* 修改censys.py UID、SECRET为你自己的api
* 设置crontab:</br>
 0 * * * *  python  /root/proxy/checkproxy.py

### 效果


