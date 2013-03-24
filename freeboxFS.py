#!/usr/bin/env python
#-*- coding: utf-8 -*-

#pip install simplejson

import fuse
import errno
import os
import stat
import time
import logging
#import argparse
#import  json
#import pprint as pp
import sys

import cookielib
import urllib2
import urllib

import shutil
import simplejson as json
#import inspect


# Specify what Fuse API use: 0.2
fuse.fuse_python_api = (0, 2)

import inspect


def datetime2timestamp(date_str, date_format="%a, %d %b %Y %H:%M:%S GMT"):
     time_tuple = time.strptime(date_str, date_format)
     timestamp = time.mktime(time_tuple)
     return timestamp


def parse_arg():
        import argparse
        parser = argparse.ArgumentParser(prog='PROG')
        parser.add_argument('--url',  action="store", dest="url",
                             help='url de la freebox revolution')
        parser.add_argument('--passwd', action="store", dest="password",
                             help='password de la freebox revolution')
        return parser.parse_args()


def get_func_name():
    outerframe = inspect.currentframe().f_back
    name = outerframe.f_code.co_name
    return name


# create logger with 'spam_application'
logger = logging.getLogger('freeboxFS')
logger.setLevel(logging.DEBUG)

# create file handler which logs even debug messages
fh = logging.FileHandler('./freeboxFS.log')
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
logger.addHandler(ch)





# Specify what Fuse API use: 0.2
fuse.fuse_python_api = (0, 2)


_file_timestamp = int(time.time())

class MyStat(fuse.Stat):         
 def __init__(self, is_dir, size,timestamp = _file_timestamp):                      

 
         fuse.Stat.__init__(self)
         self.files = []
         self.st_uid = os.getuid()                      
         self.st_gid   = os.getgid()                          
         if is_dir:                                             
              self.st_mode = stat.S_IFDIR | 0755
              self.st_nlink = 3                          
         else:                                                 
              self.st_mode = stat.S_IFREG | 0700               
              self.st_nlink = 1                               
              self.st_size = size                        
         self.st_atime = timestamp                        
         self.st_mtime = timestamp                        
         self.st_ctime = timestamp                   



class MyFS(fuse.Fuse):
                
    def __init__(self,  *args, **kw):
      try:
           # Initialize the FUSE binding's internal state.
           fuse.Fuse.__init__(self, *args, **kw)

           # Set some options required by the Python FUSE binding.
           self.flags = 0
           self.multithreaded = 0
           self.read_only = True
           
           #self.parser.add_option('--help', action='help', help="show this help message followed by the command line options defined by the Python FUSE binding and exit")
           self.parser.add_option('-v', '--verbose', action='count', dest='verbosity', default=0, help="increase verbosity")
           self.parser.add_option('--url', action="store",  dest='url', help="url de la freebox revolution")
           self.parser.add_option('--passwd', action="store", dest="password",help='password de la freebox revolution')
           self.parse()
           args_freeboxfs =  self.cmdline[0]
           print  type(args_freeboxfs.url)
           url = args_freeboxfs.url
           password = args_freeboxfs.password
           self.freebox = Freebox(url,password)

           
      except   Exception, err:
           logger.debug("%s %s %s"  %(get_func_name(),sys.exc_info()[0],str(err)))
           sys.exit(1)     



     
    def freebox(url,password):
        self.freebox = Freebox(url,password)

    def getattr(self, path):
     try:
        #path = path.encode('utf_8')
        if path == '/':
            logger.debug( "%s  %s" % (get_func_name(),path))
	    return MyStat(True, 4096)
        elif path in self.freebox.file :
           if not self.freebox.file[path] :
                 logger.debug( "%s  path: %s" % (get_func_name(),path))
                 logger.debug( "%s : %s" % (get_func_name(),str(self.freebox.url)))
                 response = urllib2.urlopen(urllib2.Request(self.freebox.url + "/get.php",urllib.urlencode({'filename' : path})))
                 headers = response.info()
                 #last_modified_time =  headers.getheader("Last-Modified")
                 last_modified_timestamp = datetime2timestamp(headers.getheader("Last-Modified")) 
                 filesize = int(response.info().getheader('Content-Length').strip())
                 return MyStat(False,filesize,last_modified_timestamp)
           else: 
                 # TODO put the correct date for directories
                 return MyStat(True,0,0)
        else :
	    return -errno.ENOENT
     except Exception, err:
            logger.debug("%s %s %s"  %(get_func_name(),sys.exc_info()[0],str(err)))

 

   
    def readdir(self, path, offset):
      try:
        logger.debug( "%s  %s offset %d" % (get_func_name(),path,offset))
        yield fuse.Direntry('.')                                                
        yield fuse.Direntry('..')
        #logger.debug("%s size self.freebox.listFile %d  ")  % (get_func_name(),len( self.freebox.listFile(path)))
        for entry in self.freebox.listFile(path) :
            logger.debug("%s  entry: %s"  % (get_func_name(),entry))
            yield fuse.Direntry(entry.encode('utf_8'))
      except :
            logger.debug(sys.exc_info()[0])


    def read(self, path, offset,size):
	print "read: path %s" % (path)
        logger.debug( "%s  %s %d %d" % (get_func_name(),path,offset,size))
	#if path == '/toto' :
        #return "Ca marche !!!!"
        self.freebox.getFile(path)
        slen = os.stat('/tmp/freeboxFS.tmp')[stat.ST_SIZE]
        #logger.debug("slen %d /tmp/freeboxFS.tmp " % (slen))
        with open('/tmp/freeboxFS.tmp') as fp:
                 fp.seek(offset)
                 buf = fp.read(size)
        return buf


class Freebox():

    def __init__(self,url,password):
        logging.debug("********************************************************"+self.__class__.__name__)
        self.file = {"/" : True, "." : True, ".." : True }
        self.size = {"/" : 2048, "." : 2048, ".." : 2048}
        self.url = url
        self.password = password
        cj = cookielib.LWPCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)
        self.authentification()

    def authentification(self):
        logreq = urllib2.urlopen(self.url+"/login.php",
		urllib.urlencode({"login":"freebox","passwd":self.password}))
        if logreq.geturl() == self.url+"/login.php":
            print "Mot de passe incorrect."
            return False
        return True

    def  listFile(self,path):
      try:
	req = urllib2.Request(self.url+"/fs.cgi",
      			'{"jsonrpc":"2.0","method":"fs.list","id":0.1778238959093924,"params":["'+path+'",{"with_attr":false}]}',
                        {"Referer": "http://mafreebox.fr/explorer.php",
                                "Content-Type": "application/json; charset=utf-8"})
	
        try:                
            statusreq = urllib2.urlopen(req)
	except urllib2.HTTPError:
            print "Erreur de Connection.\n Exit"
            exit()
            
	json_data = json.loads(statusreq.readline())
	logger.debug("%s json_data: %s" %(get_func_name(),json_data))
        #logger.debug("%s json_data[\"result\"]: %s" %(get_func_name(), json.dumps(json_data["result"])))
	for item in json_data["result"]:
		filetype = item["type"]
	        filename = item["name"]
                logger.debug("%s filename: %s" %(get_func_name(),filename))
                
                if path == "/" :
                    fullpath = "/"+filename.encode('utf-8')
                else :
                       fullpath = path+"/"+filename.encode('utf-8')
                       logger.debug("%s fullpath %s" % (get_func_name(),fullpath))
                if filetype == 'dir' : self.file[fullpath] = True
                else :
                      self.file[fullpath] = False
                      response = urllib2.urlopen(urllib2.Request(self.url+"/get.php",urllib.urlencode({'filename' : fullpath})))
		      filesize = int(response.info().getheader('Content-Length').strip())
                      self.size[fullpath]   =  filesize               
                    
                yield filename
      except Exception, err:
            logger.debug("%s %s %s"  %(get_func_name(),sys.exc_info()[0],str(err)))


    def getFile(self,path):
        logger.debug("getFile BEGIN path: %s" % (path))
        values = {'filename' : path}
        data = urllib.urlencode(values)
        req = urllib2.Request(self.url+"/get.php", data)   
        response  = urllib2.urlopen(req)
      	#shutil.copyfileobj(response, tmpFile)
        
        try:
		with open( "/tmp/freeboxFS.tmp", 'wb') as tmpFile:
			shutil.copyfileobj(response, tmpFile)
        except :
            logger.debug(sys.exc_info()[0])
         
        logger.debug("getFile END   path: %s" % (path))
        #return response.read()

def main():
    """
    This function enables using freeboxfs.py as a shell script that creates FUSE
    mount points. Execute "freeboxfs -h" for a list of valid command line options.
    """
    print "cdssdcdsccdsc"
    freeboxfs = MyFS()
    # A short usage message with the command line options defined by dedupfs
    # itself (see the __init__() method of the DedupFS class) is automatically
    # printed by the following call when sys.argv contains -h or --help.
    fuse_opts = freeboxfs.parse(['-o', 'use_ino,default_permissions,fsname=freeboxfs'] + sys.argv[1:])
    freeboxfs_opts = freeboxfs.cmdline[0]
    print "2 cdssdcdsccdsc"
    print fuse_opts 
    print "3 cdssdcdsccdsc"
    print freeboxfs_opts

    # If the user didn't pass -h or --help and also didn't supply a mount point
    # as a positional argument, print the short usage message and exit
    if freeboxfs.fuse_args.mount_expected() and not fuse_opts.mountpoint:
       freeboxfs.parse(['-h'])
    else:
        freeboxfs.parse(errex=1)
        freeboxfs.main()
   
if __name__ == '__main__':
    #main()
    
    fs = MyFS()                                                             
    #fuse_opt = fs.parse(errex=1)
    #print  fuse_opt 
    #print "cdsss"
    #print fs.cmdline[0]
    fs.main()                  
    
    #arg_result = parse_arg()
    #url = arg_result.url
    #print url
    #password = arg_result.password
    #freebox = Freebox(url,password)
    #fs = MyFS() 
    #fs.parse(errex=1)
    #fs.main()
