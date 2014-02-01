import os, sys

import time

import win32file
import win32con

import logging

_isVerbose = False # defined here to satisfy py2exe runtime issues.

verbose = False
import imp
if (hasattr(sys, "frozen") or hasattr(sys, "importers") or imp.is_frozen("__main__")):
    import zipfile
    import pkg_resources

    import re
    __regex_libname__ = re.compile(r"(?P<libname>.*)_2_7\.zip", re.MULTILINE)

    my_file = pkg_resources.resource_stream('__main__',sys.executable)
    if (verbose):
        print '%s' % (my_file)

    import tempfile
    __dirname__ = os.path.dirname(tempfile.NamedTemporaryFile().name)

    zip = zipfile.ZipFile(my_file)
    files = [z for z in zip.filelist if (__regex_libname__.match(z.filename))]
    for f in files:
        libname = f.filename
        if (verbose):
            print '1. libname=%s' % (libname)
        data = zip.read(libname)
        fpath = os.sep.join([__dirname__,os.path.splitext(libname)[0]])
        __is__ = False
        if (not os.path.exists(fpath)):
            if (verbose):
                print '2. os.mkdir("%s")' % (fpath)
            os.mkdir(fpath)
        else:
            fsize = os.path.getsize(fpath)
            if (verbose):
                print '3. fsize=%s' % (fsize)
                print '4. f.file_size=%s' % (f.file_size)
            if (fsize != f.file_size):
                __is__ = True
                if (verbose):
                    print '5. __is__=%s' % (__is__)
        fname = os.sep.join([fpath,libname])
        if (not os.path.exists(fname)) or (__is__):
            if (verbose):
                print '6. fname=%s' % (fname)
            file = open(fname, 'wb')
            file.write(data)
            file.flush()
            file.close()
        __module__ = fname
        if (verbose):
            print '7. __module__=%s' % (__module__)

        if (verbose):
            print '__module__ --> "%s".' % (__module__)

        import zipextimporter
        zipextimporter.install()
        sys.path.insert(0, __module__)

from vyperlogix.enum import Enum

from vyperlogix.misc import threadpool

from vyperlogix.misc import _utils
from vyperlogix.classes.SmartObject import SmartObject

__Q_INPUT__ = threadpool.ThreadQueue(2)
__Q_OUTPUT__ = threadpool.ThreadQueue(2)

__Q1__ = threadpool.ThreadQueue(100)
__Q2__ = threadpool.ThreadQueue(100)

class Actions(Enum.Enum):
    UNKNOWN = -1
    Created = 1
    Deleted = 2
    Updated = 3
    Renamed_From = 4
    Renamed_To = 5

def __terminate__():
    import os
    from vyperlogix.process.killProcByPID import killProcByPID
    pid = os.getpid()
    killProcByPID(pid)

def report_changes(cflags):
    flags = []
    if (cflags & win32con.FILE_NOTIFY_CHANGE_FILE_NAME):
        flags.append('FILE_NOTIFY_CHANGE_FILE_NAME')
    if (cflags & win32con.FILE_NOTIFY_CHANGE_DIR_NAME):
        flags.append('FILE_NOTIFY_CHANGE_DIR_NAME')
    if (cflags & win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES):
        flags.append('FILE_NOTIFY_CHANGE_ATTRIBUTES')
    if (cflags & win32con.FILE_NOTIFY_CHANGE_SIZE):
        flags.append('FILE_NOTIFY_CHANGE_SIZE')
    if (cflags & win32con.FILE_NOTIFY_CHANGE_LAST_WRITE):
        flags.append('FILE_NOTIFY_CHANGE_LAST_WRITE')
    if (cflags & win32con.FILE_NOTIFY_CHANGE_SECURITY):
        flags.append('FILE_NOTIFY_CHANGE_SECURITY')
    print >> sys.stdout, 'INFO: %s' % ('FLAGS: %s --> %s' % (format(cflags,'b'),flags))

def date_comparator(a, b):
    a_statinfo = os.stat(a)
    b_statinfo = os.stat(b)
    print 'DEBUG: a=%s, b=%s' % (a,b)
    return -1 if (a_statinfo.st_mtime < b_statinfo.st_mtime) else 0 if (a_statinfo.st_mtime == b_statinfo.st_mtime) else 1

@threadpool.threadify(__Q_INPUT__)
def handle_inputs(hDir,changes,watching,output=None,callback=None,is_running=True):
    _files_ = [f for f in [os.path.join(watching,n) for n in os.listdir(watching)] if (os.path.isfile(f))]
    _files_.sort(date_comparator)
    
    def __handle_file__(a,w,f,out=None):
	if (callable(callback)):
	    try:
		time.sleep(1) # mitigate a possible race condition - don't want to consume the file too quickly... LOL
		callback(a,w,f,output=out)
	    except Exception, ex:
		print >> sys.stderr, 'EXCEPTION: %s' % (_utils.formattedException(details=ex))
    
    for f in _files_:
	action = Actions.Created
	__handle_file__(action, watching, os.path.basename(f), out=output)

    while (is_running):
        for action,aFile in win32file.ReadDirectoryChangesW(hDir,1024,True,changes,None,None):
            action = Actions(action)
	    __handle_file__(action, watching, aFile, out=output)

@threadpool.threadify(__Q2__)
def ProcessFile(fpath,output=None):
    if (fpath and os.path.exists(fpath) and (os.path.isfile(fpath))):
	if (output and os.path.exists(output) and os.path.isdir(output)):
	    try:
		dest = os.sep.join([output,os.path.basename(fpath)])
		_utils.copyFile(fpath, dest, no_shell=True)
		print >> sys.stdout, 'DEBUG: PROCESS --> %s --> %s' % (fpath,dest)
		if (os.path.exists(dest)):
		    os.remove(fpath)
	    except Exception, ex:
		print >> sys.stderr, 'EXCEPTION: %s' % (_utils.formattedException(details=ex))

@threadpool.threadify(__Q1__)
def ProcessInputs(action,watching,fpath,output=None):
    fp = '/'.join([watching, fpath]).replace(os.sep,'/')
    if (action == Actions.Created):
	print >> sys.stdout, 'DEBUG: PROCESS --> INPUT (%s) --> %s' % (action,fp)
	ProcessFile(fp,output=output)
    else:
	print >> sys.stdout, 'DEBUG: IGNORE --> INPUT (%s) --> %s' % (action,fp)

if (__name__ == '__main__'):
    from optparse import OptionParser
    
    if (len(sys.argv) == 1):
	sys.argv.insert(len(sys.argv), '-h')
    
    parser = OptionParser("usage: %prog [options]")
    parser.add_option('-v', '--verbose', dest='verbose', help="verbose", action="store_true")
    parser.add_option("-i", "--input", action="store", type="string", dest="ipath")
    parser.add_option("-o", "--output", action="store", type="string", dest="opath")
    
    options, args = parser.parse_args()
    
    _isVerbose = False
    if (options.verbose):
	_isVerbose = True
	
    __ipath__ = None
    if (options.ipath and os.path.exists(options.ipath) and os.path.isdir(options.ipath)):
	__ipath__ = options.ipath
	
    if (_isVerbose):
	print >> sys.stdout, 'INFO: input path is "%s".' % (__ipath__)
	
    __opath__ = None
    if (options.opath and os.path.exists(options.opath) and os.path.isdir(options.opath)):
	__opath__ = options.opath
	
    if (_isVerbose):
	print >> sys.stdout, 'INFO: output path is "%s".' % (__opath__)

    __changes__ = 0
    __hDir__ = None
	
    if (__ipath__ and os.path.exists(__ipath__) and os.path.isdir(__ipath__)):
	FILE_LIST_DIRECTORY = 0x0001
	__hDir__ = win32file.CreateFile (
            __ipath__,
            FILE_LIST_DIRECTORY,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
            None,
            win32con.OPEN_EXISTING,
            win32con.FILE_FLAG_BACKUP_SEMANTICS,
            None
        )
	#__changes__ = win32con.FILE_NOTIFY_CHANGE_FILE_NAME
	#__changes__ |= win32con.FILE_NOTIFY_CHANGE_DIR_NAME
	#__changes__ |= win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES
	#__changes__ |= win32con.FILE_NOTIFY_CHANGE_SIZE
	#__changes__ |= win32con.FILE_NOTIFY_CHANGE_LAST_WRITE
	#__changes__ |= win32con.FILE_NOTIFY_CHANGE_SECURITY

	__changes__ = win32con.FILE_NOTIFY_CHANGE_FILE_NAME
	
	report_changes(__changes__)

	handle_inputs(__hDir__, __changes__, __ipath__, output=__opath__, callback=ProcessInputs)
	
	while (1):
	    print >> sys.stdout, 'Sleeping...'
	    time.sleep(5)
	    print >> sys.stdout, 'Doing nothing...'
	    time.sleep(5)
    else:
	print >> sys.stderr, 'WARNING: Cannot proceed without an input path, see the --input parameter.'
