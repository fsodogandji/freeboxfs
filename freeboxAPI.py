#-*- coding: utf-8 -*-

import logging
import httplib2
import urllib
import inspect 

import sys
import simplejson as json 
import requests
from bs4 import BeautifulSoup
import sys


def get_func_name():
    outerframe = inspect.currentframe().f_back
    name = outerframe.f_code.co_name
    return name



# create logger with 'spam_application'
logger = logging.getLogger('freeboxFS')
logger.setLevel(logging.DEBUG)

# create file handler which logs even debug messages
fh = logging.FileHandler('./test_freeboxAPI.log')
fh.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)
#logger.addHandler(ch)






class Freebox():

    def __init__(self,url,password):
        #logging.debug("********************************************************"+self.__class__.__name__)
        self.file = {"/" : True, "." : True, ".." : True }
        self.size = {"/" : 2048, "." : 2048, ".." : 2048}
        self.treefile = dict() 
        self.timestamp = {}
        self.url = url
        self.password = password
        self.client = requests.session()    

        
        form =  {"login":"freebox","passwd":password}
        r = self.client.post(url+'/login.php',data =form ,headers= {'Content-type': 'application/x-www-form-urlencoded'})
        print "COOKIES", r.cookies['FBXSID']
        soup =  BeautifulSoup(r.text)
        #r_csrf_token =  soup.find('input',dict(name='csrf_token'))['value']
        #print "_csrf_token", r_csrf_token

    def rmdir(self,path):
         logger.debug( "%s %s" % (get_func_name(),path))
         try:
	    req = urllib2.Request(self.url+"/fs.cgi",
                '{"jsonrpc":"2.0","method":"fs.remove","params":["'+path+'"]}',
                 {"Referer": "http://mafreebox.fr/explorer.php",
                "Content-Type": "application/json; charset=utf-8"})
            logger.debug( "s% req: %s  " % (get_func_name(),req))
            statusreq = urllib2.urlopen(req).readline()
            logger.debug( "s% statusreq: %s  " % (get_func_name(),statusreq))
            self.file[path] = True
         except Exception, err:
		 logger.debug("%s %s %s"  %(get_func_name(),sys.exc_info()[0],str(err)))
                 top = traceback.extract_stack()[-1]
                 logger.debug("%s" %(', '.join([type(e).__name__, os.path.basename(top[0]), str(top[1])])))

    def mkdir(self,path):
          logger.debug( "%s %s" % (get_func_name(),path))
          try:
	    req = urllib2.Request(self.url+"/fs.cgi",
                '{"jsonrpc":"2.0","method":"fs.mkdir","params":["'+path+'"]}',
                 {"Referer": "http://mafreebox.fr/explorer.php",
                "Content-Type": "application/json; charset=utf-8"})
            logger.debug( "s% req: %s  " % (get_func_name(),req))
            statusreq = urllib2.urlopen(req).readline()
            logger.debug( "s% statusreq: %s  " % (get_func_name(),statusreq))
            self.file[path] = True
          except Exception, err:
		 logger.debug("%s %s %s"  %(get_func_name(),sys.exc_info()[0],str(err)))
                 top = traceback.extract_stack()[-1]
                 logger.debug("%s" %(', '.join([type(e).__name__, os.path.basename(top[0]), str(top[1])])))




                 


    def  readdir(self,path):
       
      try:
        form_request = '{"jsonrpc":"2.0","method":"fs.list","params":["'+path+'",{"with_attr":true}]}'
        
        rp = self.client.post(self.url+"/fs.cgi",data=form_request,headers= {'Content-Type': 'application/json; charset=iso-8859-1'}) 
        json_data = json.loads(rp.text)
        
        
	logger.debug("%s json_data: %s" %(get_func_name(),json_data))
        
	for item in json_data["result"]:
		filetype = item["type"]
	        filename = item["name"]

                logger.debug("%s filename: %s" %(get_func_name(),filename))
                
                if path == "/" : fullpath = "/"+filename.encode('utf-8')
                else :           fullpath = path+"/"+filename.encode('utf-8')

                logger.debug("%s fullpath %s" % (get_func_name(),fullpath))
                
                """
                self.treefile[fullpath]['timestamp']  = item['modification']
                self.treefile[fullpath]['size']       = item['size']
                self.treefile[fullpath]['type']       = item["type"]
                """
                self.treefile[fullpath] = item
                self.treefile['/'] = { 'modification': 1365279471, 'type': 'dir', 'name': '/', 'size': 4096}
                self.size[fullpath]   =  item['size'] 
                self.timestamp[fullpath] = item['modification']
                if filetype == 'dir' :
                        self.file[fullpath] = True
                else :
                      self.file[fullpath] = False
                logger.debug("self.treefile %s  %s" % (get_func_name(),self.treefile)) 
                logger.debug("yield filename %s  %s" % (get_func_name(),filename))
                yield filename
      except Exception, err:
            logger.debug("%s %s %s"  %(get_func_name(),sys.exc_info()[0],str(err)))


    def getFile(self,path):
        logger.debug("getFile BEGIN path: %s" % (path))
       
        r = self.client.post(self.url+"/get.php", data ={'filename' : path} ,  stream=True)
        FD  = open("/tmp/fuse.tmp",'wb')  
        for chunk in r.iter_content(8*1024):
              FD.write(chunk)
        FD.close()      
        logger.debug("getFile END   path: %s" % (path))
        #return response.read()
