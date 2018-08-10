## All functions related to suites

import os

'''
returns: users home cylc run directory
'''
def cylc_run_dir():
    return os.path.expanduser(
        os.path.join('~', 'cylc-run')
    )

'''
@param {str} suitename, 
returns: all attributes out of contact file for suite
'''
def contact_file(suitename):
    suite_vars = {}
    with open(os.path.join(service_dir(suitename), 'contact'), 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            suite_vars[key] = value
    return suite_vars

'''
@param {str} suitename
returns: path of .service file for a suite with *suitename*
'''
def service_dir(suitename):
    return os.path.join(
        cylc_run_dir(), suitename, '.service'
    )

'''
@param {str} suite, the name of the suite 
returns: the passphrase as read from the file saved in the '.service/passphrase'
TODO: dynamically retrieve passphrase file, error check path, os build path rather than concat
'''
def get_passphrase(suite):
    with open(os.path.join(service_dir(suite), 'passphrase'),'r') as f:
       	passphrase = f.readline()
    return passphrase

'''
@param {str} suite, the name of the suite 
@param {str} [path = None], the base path to the certificate 
returns: the path to the signed server certificate
TODO: dynamically retrieve passphrase file, error check path, os build path rather than concat
'''
def get_verify(suite, path=None):
    return os.path.join(service_dir(suite), 'ssl.cert')


def is_suite(dir_):
    path = os.path.join(cylc_run_dir(),dir_, "suite.rc")
    if os.path.isfile(path):
        return True;
    return False;

def is_running(dir_):
    path = os.path.join(cylc_run_dir(),dir_, ".service/contact")
    if os.path.isfile(path):
        return True;
    return False;

