'''
    author: Nancy Gomez
    FILE: au.py
    PURPOSE: establish secure connection to cylc running instance
    PRECONDITIONS: A running instance of CYLC, the hostname, port number, passphrase,
    and certificate of the suite. Iorder to view these simply check your "concat"
    file within your suite folder. Might be something like cylc-run/my.suite/.services
'''
from __future__ import unicode_literals
import os
import json

import requests
from anytree import Node, RenderTree
from job import Job, JobNode
from port import getPorts


HOST_NAME = 'localhost'

def cylc_run_dir():
    return os.path.expanduser(
        os.path.join('~', 'cylc-run')
    )

def contact_file(suitename):
    suite_vars = {}
    with open(os.path.join(service_dir(suitename), 'contact'), 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            suite_vars[key] = value
    return suite_vars

def service_dir(suitename):
    return os.path.join(
        cylc_run_dir(), suitename, '.service'
    )


'''
    Returns the passphrase as read from the file saved in the '.service/passphrase'
    @param {str} suite, the name of the suite 
    TODO: dynamically retrieve passphrase file, error check path, os build path rather than concat
'''
def get_passphrase(suite):
    with open(os.path.join(service_dir(suite), 'passphrase'),'r') as f:
       	passphrase = f.readline()
    return passphrase


'''
    Returns an array of the jobs already in display order
    @param {JSON} suite_json, The returned JSON from the request to 'get_latest_state'
    @param {dict} cycles, The cycle hierarchy for the jobs
'''
def get_family_hierarchy(suite_json, cycles):
    ancestors = suite_json["ancestors_pruned"]
    cycle_trees = {}
    groupings = {}
    for cycle, jobs in sorted(cycles.items()):
      # add a root cycle node to the dictionary 
      cycle_trees[cycle] = JobNode(cycle, Job(**{'name': cycle, 'is_group' : True}))
      
      # iterate through this cycle's jobs
      for job in jobs:
        # these values reset for each job
        order = ancestors[job.name]
        root = cycle_trees[cycle]
        parent_id = root.id
        
        # if the job has a family grouping / parent 
        if (len(order) > 2):
          
          # iterate through its family in reverse (excluding first and last)
          for element in reversed(order[1:-1]):
            # for unique ids we need the name and it's parent's name 
            group_id = element + parent_id
            
            # create a new grouping if it doesn't already exist
            if group_id not in groupings:
              groupings[group_id] = JobNode(group_id, Job(**{'name': element, 'is_group' : True}), parent = root)
              
            # connect only if last item
            if (element == order[1]):
              JobNode(job.name + job.label, job, parent = groupings[group_id])
            
            # update parent for the next one
            root = groupings[group_id]
            parent_id = root.id
              
        # otherwise job just goes under root cycle node
        else:
          JobNode(job.name + job.label, job, parent = root)
    
    # TODO: figure out how to traverse tree in jinja2 instead of having to put tree
    # into another array to increase efficiency
    hierarchy = []
    for cycle_key, cycle_node in cycle_trees.items():
      for pre, fill, node in RenderTree(cycle_node):
          node.job.indent = node.depth
          hierarchy.append(node.job)
        #   print("%s%s %d" % (pre, node.job.own_id, node.job.indent))
        
    # for item in hierarchy:
    #   print '    ' * item.indent + repr(item)
    return hierarchy

'''
    Returns a dictionary of string keys and Job Array values
    @param {JSON} suite_json, The returned JSON from the request to 'get_latest_state'
'''
def parse_jobs(suite_json):
    cycle_hierarchy = {}
    index = 0
    for job, job_dict in suite_json["summary"][1].items():
        new_job = Job(**job_dict)
        # jobs.append(new_job)
        if cycle_hierarchy.has_key(new_job.label):
            cycle_hierarchy[new_job.label].append(new_job)
        else:
            cycle_hierarchy[new_job.label] = [new_job]
        index += 1
    return cycle_hierarchy

'''
    Returns the path to the signed server certificate
    @param {str} suite, the name of the suite 
    @param {str} [path = None], the base path to the certificate 
    TODO: dynamically retrieve passphrase file, error check path, os build path rather than concat
'''
def get_verify(suite, path=None):
    return os.path.join(service_dir(suite), 'ssl.cert')

'''
    Returns an array of Job objects and a dictionary of strings, JobNodes as a tuple
    TODO: seperate API call from actual parsing of returned value
'''

def save_json_to_model(json_to_save):
    from models import JSONTracker 
    from django.utils import timezone 
    latest_json = JSONTracker(json=json_to_save, date_added=timezone.now())
    latest_json.save()
    return

def get_latest_state_id():
    from models import JSONTracker
    doc_id = JSONTracker.objects.latest('date_added').id
    return doc_id

def get_state_by_id(state_id):
    from models import JSONTracker
    state = JSONTracker.objects.get(id=state_id)
    return state.json


def diff_state(client_state, current_state):
    if client_state is current_state:
        return None
    if isinstance(current_state, list):
        if cmp(client_state, current_state) is 0:
            return None
        result = []
        for i in range(len(current_state)):
            result.append(diff_state(client_state[i], current_state[i]))
        return result
    if isinstance(current_state, dict):
        if cmp(client_state, current_state) is 0:
            return None
        result = {}
        for i in client_state.keys():
            diff = diff_state(client_state[i], current_state[i])
            if i not in current_state.keys():
                result[i] = None
            elif diff is None:
                continue
            else:
                result[i] = diff
        for i in current_state.keys():
            if i not in client_state.keys():
                result[i] = current_state[i]
        return result
    return current_state


def get_jobs_from_response(response):
    from job import Job
    jobs = []
    for job in response:
        jobs.append(job.as_dict())
    return jobs 


def get_response(suitename):
    contact = contact_file(suitename)
    port = contact['CYLC_SUITE_PORT']
    host = contact['CYLC_SUITE_HOST']
    auth = requests.auth.HTTPDigestAuth('cylc', get_passphrase(suitename))
    session = requests.Session()
    url = "https://%s:%s/get_latest_state" % (host, port)
    try:
        ret = session.get(
                            url,
                            auth = auth,
                            verify = get_verify(suitename)
                         )
    
        response = ret.json()
        save_json_to_model(response)
        cycles = parse_jobs(response)
        hierarchy = get_family_hierarchy(response, cycles)
        return hierarchy
    except Exception, err: 
        print err
