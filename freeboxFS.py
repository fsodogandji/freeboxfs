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
import  traceback, os.path
import httplib2
from collections import defaultdict
import requests

# Specify what Fuse API use: 0.2
fuse.fuse_python_api = (0, 2)

import inspect

from  freeboxAPI import Freebox

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
           self.filetreeFS = defaultdict(dict)
           self.filetreeFS['/'] = { 'modification': 1365279471, 'type': 'dir', 'name': '/', 'size': 4096}
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

        if path == '/':
            logger.debug( "%s  %s" % (get_func_name(),path))
	    return MyStat(True, 4096)
        elif path in self.freebox.file :
       
                 logger.debug( "%s  path: %s" % (get_func_name(),path))
                 logger.debug( "%s : %s" % (get_func_name(),str(self.freebox.url)))
#                 last_modified_timestamp = self.freebox.timestamp[path]
#                 filesize = self.freebox.size[path] 
                 return MyStat(self.freebox.file[path], self.freebox.size[path],self.freebox.timestamp[path])
        else :
	    return -errno.ENOENT
     except Exception, err:
            logger.debug("%s %s %s"  %(get_func_name(),sys.exc_info()[0],str(err)))

    def mkdir(self,path,mode):
        logger.debug( "path: %s mode: %s" % (get_func_name(),path))	
        self.freebox.mkdir(path)


   
    def readdir(self, path, offset):
      try:
        logger.debug( "%s  %s offset %d" % (get_func_name(),path,offset))
        yield fuse.Direntry('.')                                                
        yield fuse.Direntry('..')
        #logger.debug("%s size self.freebox.readdir %d  ")  % (get_func_name(),len( self.freebox.readdir(path)))
        self.freebox.readdir(path)
        for entry in self.freebox.readdir(path) :
            logger.debug("%s  entry: %s"  % (get_func_name(),entry))
            yield fuse.Direntry(entry.encode('utf_8'))
      except :
            logger.debug(sys.exc_info()[0])


    def open(self, path, flags):
        logger.debug( "%s  %s %s" % (get_func_name(),path,flags))
        if path not in self.freebox.file:
             return -errno.ENOENT
        self.freebox.getFile(path)
        return open("/tmp/fuse.tmp", "rb")


    def read(self, path, size, offset, fh):
        logger.debug( "%s  %s %s" % (get_func_name(),path,fh.name))
        fh.seek(offset)
        return fh.read(size)


    def release(self, path, flags, fh):
        logger.debug( "%s  %s %s" % (get_func_name(),path,str(flags)))
        fh.close()
        os.unlink(fh.name)        


def main():
    """
    This function enables using freeboxFS.py as a shell script that creates FUSE
    mount points. Execute "freeboxfs -h" for a list of valid command line options.
    """
    freeboxfs = MyFS()
    # A short usage message with the command line options defined by dedupfs
    # itself (see the __init__() method of the DedupFS class) is automatically
    # printed by the following call when sys.argv contains -h or --help.
    fuse_opts = freeboxfs.parse(['-o', 'use_ino,default_permissions,fsname=freeboxfs'] + sys.argv[1:])
    freeboxfs_opts = freeboxfs.cmdline[0]
    print fuse_opts 
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
