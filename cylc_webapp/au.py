from __future__ import unicode_literals
import pdb
import json
import requests
import suites
from collections import defaultdict

'''
returns: a defaultdict that sets any keys that don't exist to another defaultdict
'''
def new_dd():
    return defaultdict(new_dd)

'''
@param {dict} nodes, all of the nodes to be inserted into tree 
@param {dict} ancestors, a dictionary of all ancestors of each job
@param {defaultdict} tree, a nested dictionary of the tree of processes
returns: a nested dictionary with the hierarchy of all jobs
'''
def build_tree(nodes, ancestors, tree = defaultdict(new_dd)):
    for node, data in nodes.iteritems():
        path = ancestors[data['name']][::-1]
        path[0] = data['label']
        if(len(path) > 1):
            for i in range(0, len(path)*2 -1):
                if i % 2 == 1:
                    path.insert(i, "children")
        inner_dict = gen_dict_keys_using_list(tree, path[:-1])
        try: 
            children = inner_dict[path[-1]]['children']
        except:
            children = {}
        inner_dict[path[-1]] = {'data':data, 'children':children}
    return tree


def build_flattened_dict(nodes, ancestors):
    tree = {}
    for node, data in nodes.iteritems():
        path = ancestors[data['name']][::-1]
        path[0] = data['label']
        if data['name'] == 'root':
            data['name'] = data['label']
        path = ".".join(path)
        tree[path] = data
    return tree 


'''
@param {str} json_to_save, A json of jobs to save to TextField in django model
returns: true if it successfully saved the JSON to the model, false otherwise
'''
def save_json_to_model(json_to_save):
    from models import JSONTracker 
    from django.utils import timezone 
    try:
        latest_json = JSONTracker(json=json_to_save, date_added=timezone.now())
        latest_json.save()
        return True
    except:
        return False

'''
returns: the id {int} of the JSONTracker object that was most recently saved
'''
def get_latest_state_id():
    from models import JSONTracker
    doc_id = JSONTracker.objects.latest('date_added').id
    return doc_id


'''
@param {dict} ancestors, tree/hierarchy of all jobs/children
@param {list} keys, all parents to get to child in tree
returns: object at last key in *keys* from *ancestors* this allows
addition of more objects at that key
'''
def gen_dict_keys_using_list(ancestors, keys):
    import operator
    from functools import reduce

    return reduce(operator.getitem, keys, ancestors)

'''
@param {int} state_id
returns: a json from the JSONTracker object with *state_id*
'''
def get_state_by_id(state_id):
    from models import JSONTracker
    state = JSONTracker.objects.get(id=state_id)
    return state.json

'''
@param {str} suitename
returns: a json with all info about *suitename* from cylc
'''
def get_cylc_data(suitename):
    contact = suites.contact_file(suitename)
    port = contact['CYLC_SUITE_PORT']
    host = contact['CYLC_SUITE_HOST']
    auth = requests.auth.HTTPDigestAuth('cylc', suites.get_passphrase(suitename))
    session = requests.Session()
    url = "https://%s:%s/get_latest_state" % (host, port)
    try:
        ret = session.get(
                            url,
                            auth = auth,
                            verify = suites.get_verify(suitename)
                         )
    
        response = ret.json()
        return response
    except Exception as e:
        return e

def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z
        
def get_jobs_from_cylc_data(response):
    parents = build_flattened_dict(response['summary'][2], response['ancestors'])
    children = build_flattened_dict(response['summary'][1], response['ancestors'])
    jobs_tree = merge_two_dicts(parents, children) 
    save_json_to_model(jobs_tree)
    return sorted(jobs_tree.items())

def get_child_counts(ancestors):
    child_counts = {} 
    for child, ancestor_list in ancestors.iteritems():
        # pop first item because it is an ancestor of itself
        child_counts[child] = 0
        ancestor_list.pop(0)
        for ancestor in ancestor_list:
            child_counts[ancestor] += 1
    return child_counts


def get_full_response(suitename):
    try:
        from collections import OrderedDict
        response = get_cylc_data(suitename)
        jobs = OrderedDict(get_jobs_from_cylc_data(response))
        child_counts = get_child_counts(response['ancestors'])
        return jobs, child_counts
    except Exception as e:
        return "Couldn't get information for " + suitename
    

'''
@param {str} suitename
returns: a json with a hierarchy of all jobs and their children, no additional
cylc information is returned
'''
def get_cylc_jobs(suitename):
    try:
        response = get_cylc_data(suitename)
        from collections import OrderedDict
        return OrderedDict(get_jobs_from_cylc_data(response))
    except Exception as e:
        print(e)
        return "Couldn't get information for " + suitename

