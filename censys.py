#!/usr/bin/env python
#coding:utf-8

import json
import requests
import sys
import time
import datetime
import threading
import dbconnect
import Queue
reload(sys)
sys.setdefaultencoding("utf-8")


API_URL = "https://www.censys.io/api/v1/search/"
UID = "UID"
SECRET = "SECRET"



class CheckIp(threading.Thread):

    def __init__(self,queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.lock = threading.Lock()
        global exitFlag
    def run(self):
        while not exitFlag.is_set():
            if self.queue.empty():
                time.sleep(30)
            else:
                try:
                    get = self.queue.get()
                    get = get.split(':')
                    ip = get[0]
                    port = int(get[1])
                    self.checkProxy(ip,port)
                except Exception,e:
                    print e
    def checkProxy(self,ip,port):
        end = 0
        proxy = 0
        https = 0
        try:
            start = time.clock()
            proxies = {"http":"http://%s:%s"%(ip,port),"https": "http://%s:%s"%(ip,port)}
            r1 = requests.get("http://www.baidu.com/img/baidu_jgylogo1.gif", proxies=proxies,timeout=10)
            if int(r1.headers['Content-Length']) == 708:
                proxy =1
                end = time.clock()
                speed = str(end-start)[:4]
                '''
                r2 = requests.get("https://www.baidu.com", proxies=proxies,timeout=10)
                if int(r2.status_code) == 200:
                    https=1
                '''
        except Exception,e:
            pass
        finally:
            self.queue.task_done()    
        if proxy:
            self.saveDate(ip,port,https,speed)
    def saveDate(self,ip,port,https,speed):
        self.lock.acquire()
        print '[*]Found Proxy: %s' %(ip+':'+str(port)) 
        try:
            self.conn.ping()
        except Exception,e:
            self.conn = dbconnect.connection()
            self.cur = self.conn.cursor()
        sql = "insert into `proxy` (`ipaddr`,`port`,`https`,`speed`,`type`,`utime`,`status`) values('%s','%s','%s','%s','%s','%s','%s') on duplicate key update `port`='%s',`type`='%s',`speed`='%s',`utime`='%s',`status`='%s'" % (ip,port,https,speed,2,time.strftime('%Y-%m-%d'),1,port,2,speed,time.strftime('%Y-%m-%d'),1)
        try:
            self.cur.execute(sql)
        except Exception,e:
            print e
        finally:
            self.cur.close()
            self.conn.close()
            self.lock.release()


class GetIp(threading.Thread):

    def __init__(self,queue,startpage,endpage,key,portlist):
        threading.Thread.__init__(self)
        self.queue = queue
        self.startpage = startpage
        self.endpage = endpage
        self.key = key
        self.portlist = portlist
        global exitFlag
    def run(self):
        for i in range(self.startpage,self.endpage+1):
            self.getIpaddr(i)

    def getIpaddr(self,page):
        try:
            query = {"query":self.key,"page":page}
            if page % 118 == 0:
                time.sleep(60*5)
            print '[*]Get Page: %s' % (page)
            res = requests.post(API_URL+"ipv4",data=json.dumps(query),auth=(UID, SECRET),timeout=10)
            res_results = res.json()
            for i in res_results['results']:
                for p in self.portlist:
                    self.queue.put((i['ip']+':'+str(p)),True)
            time.sleep(1)
        except Exception,e:
            print '[*]Get Page: %s Error' % (page)
            time.sleep(60)
  
def main():
    print '[*]Start'
    global exitFlag
    threads = []
    queue = Queue.Queue(10000)
    keyword = ['Squid','CCProxy','Tinyproxy','Wingate','Pound','Proxy','Mikrotik']
    portlist = [8080,80,3128]
    for key in keyword:
        exitFlag.clear()
        print '[*]Use Keyword: %s' %(key)
        query = {"query":key,"page":1}
        try:
            res = requests.post(API_URL+"ipv4",data=json.dumps(query),auth=(UID,SECRET),timeout=30)
            res_results = res.json()
            endpage = res_results['metadata']['pages']
            print '[*]Total Page: %s' %(endpage)
            startpage = 1
            g = GetIp(queue,startpage,endpage,key,portlist)
            g.start()
            for i in range(200):
                t = CheckIp(queue)
                t.setDaemon(True)
                t.start()
            g.join()
            queue.join()
            exitFlag.set()
            print '[*]Keyword:%s Is Done' %(key)
            time.sleep(60)
        except Exception,e:
            print '[*]Keyword:%s Error' %(key)
    print '[*]All Done...'

if __name__ == "__main__":
    exitFlag = threading.Event()
    while 1:
        main()
        time.sleep(60*60*24)

