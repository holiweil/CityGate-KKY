'''
Tento modul slouzi k ziskani dodatecnych nepovinnych parametru z prikazoveho radku.

Autor: Jan Holecek
'''

import sys, getopt


def getParam(name):
    param = ''
    try:
	opts, args = getopt.getopt(sys.argv[2:], "a:p:k:v:i:", []) #prvnim parametrem je parametr server/client
    except getopt.error, msg:
	print msg
	sys.exit(2)
    for o, a in opts:
	if o in ("-p", "--port"):
            if name == 'port':param = int(a)
            else: pass
	if o in ("-a", "--address"):
	    if name == 'address':param = a
            else: pass
	if o in ("-k", "--kinnect"):
	    if name == 'kinect':param = int(a)
            else: pass
        if o in ("-v", "--videoport"):
	    if name == 'videoport':param = int(a)
            else: pass
        if o in ("-i", "--idkinect"):
	    if name == 'idkinect':param = int(a)
            else: pass
    return param
