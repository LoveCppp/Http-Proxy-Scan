#!/usr/bin/env python
#coding:utf-8

import json
import requests
import sys
import time
import datetime
import threading
import Queue
import dbconnect
reload(sys)
sys.setdefaultencoding("utf-8")


class checkProxy(threading.Thread):

    def __init__(self,queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.lock = threading.Lock()
    def run(self):
        while not self.queue.empty():
            iplist = self.queue.get()
            self.queue.task_done()
            ip = iplist[0]
            port = int(iplist[1])
            self.check(ip,port)
    def check(self,ip,port):
        status = 0
        end = 0
        proxy = 0
        https = 0
        speed = 0
        count = 3
        while count:
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
            if proxy:
                status = 1 
                print '[*]Alive: '+ip+':'+str(port)
                self.update(status,ip,https,speed)
                break
            else:
                count = count-1
                if count == 0:
                    print '[*]Dead: '+ip+':'+str(port)
                    self.update(status,ip,https,speed)
    def update(self,status,ip,https,speed):
        self.lock.acquire()
        try:
            self.conn.ping()
        except Exception,e:
            self.conn = dbconnect.connection()
            self.cur = self.conn.cursor()
        if status == 1:
            sql = "update `proxy` set `https`='%s',`speed`='%s',`utime`='%s',`status`='%s' where `ipaddr`='%s'" %(https,speed,time.strftime('%Y-%m-%d'),1,ip)
        else:
            sql = "update `proxy` set `status`='%s' where `ipaddr`='%s'" %(0,ip)
        try:
            self.cur.execute(sql)
        except Exception,e:
            print e
        finally:
            self.cur.close()
            self.conn.close()
            self.lock.release()

def main():
    print '[*]Start'
    queue = Queue.Queue()
    threads = []
    conn = dbconnect.connection()
    cur = conn.cursor()
    sql = "select ipaddr,port from proxy where status=1"
    cur.execute(sql)
    alldata = cur.fetchall()
    cur.close()
    conn.close()
    for i in alldata:
        queue.put(i)
    for j in range(50):
        t = checkProxy(queue)
        threads.append(t)
        t.start()
    queue.join()
    for t in threads:
        t.join(60)
    print '[*]Done...'
if __name__ == "__main__":
    main()

