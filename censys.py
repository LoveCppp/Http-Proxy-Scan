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
        global singal,exitFlag
    def run(self):
        while not exitFlag.is_set():
            if self.queue.empty():
                singal.wait()
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
                r2 = requests.get("https://www.baidu.com", proxies=proxies,timeout=10)
                if int(r2.status_code) == 200:
                    https=1
        except Exception,e:
            pass
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
        global singal,exitFlag
    def run(self):
        try:
            for i in range(self.startpage,self.endpage+1):
                if self.queue.qsize()>10000:
                    time.sleep(60*2)
                print '[*]Get Page: %s' % (i)
                self.getIpaddr(i)
                if self.queue.qsize()>=1:
                    if singal.is_set():
                        pass
                    else:
                        singal.set()
                if i == self.endpage:
                    while 1:
                        if self.queue.empty():
                            exitFlag.clear()
                            exitFlag.set()
                            break
                        time.sleep(30)
        except Exception,e:
            print e
    def getIpaddr(self,page):
        query = {"query":self.key,"page":page}
        if page % 118 == 0:
            time.sleep(60*5)
        try:
            res = requests.post(API_URL+"ipv4",data=json.dumps(query),auth=(UID, SECRET),timeout=10)
            res_results = res.json()
            for i in res_results['results']:
                for p in self.portlist:
                    self.queue.put(i['ip']+':'+str(p))
            time.sleep(1)
        except Exception,e:
            print '[*]Get Page: %s Error' % (page)
            time.sleep(60)
  
def main():
    print '[*]Start'
    global singal,exitFlag
    threads = []
    queue = Queue.Queue()
    keyword = ['Squid','CCProxy','Tinyproxy','Wingate','Pound','Proxy','Mikrotik']
    portlist = [8080,80,3128]
    for key in keyword:
        exitFlag.clear()
        singal.clear()
        print '[*]Use Keyword: %s' %(key)
        query = {"query":key,"page":1}
        try:
            res = requests.post(API_URL+"ipv4",data=json.dumps(query),auth=(UID,SECRET),timeout=30)
            res_results = res.json()
            endpage = res_results['metadata']['pages']
        except Exception,e:
            print '[*]Keyword:%s Error %s' %(key,e)
        print '[*]Total Page: %s' %(endpage)
        startpage = 1
        g = GetIp(queue,startpage,endpage,key,portlist)
        g.start()
        for i in range(150):
            t = CheckIp(queue)
            threads.append(t)
            t.start()
        g.join()
        for t in threads:
            t.join()
        queue.join()
        print '[*]Keyword:%s Is Done' %(key)
        time.sleep(60)
    print '[*]All Done...'

if __name__ == "__main__":
    exitFlag = threading.Event()
    singal = threading.Event()
    while 1:
        main()
        time.sleep(60*60*24)