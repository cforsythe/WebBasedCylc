# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.template import loader

import os

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from suites import cylc_run_dir 

'''
This function is called by register.html

returns: an html page with a form for 
registering a new suite
'''
def register(request):
    template = loader.get_template('register.html')
    return HttpResponse(template.render())

'''
This function is called by suites.html to load all directories
that have a suite.rc file. This is so user can choose one of 
the suites to view information on.

returns: an html page with all directories rendered into the page
using django templates
'''
def suites(request):
    from suites import is_suite
    dirs_with_suite = list()
    dirs = os.listdir(cylc_run_dir())
    for direc in dirs:
        if is_suite(direc):
            dirs_with_suite.append(direc)
    context = {
        "suites": dirs_with_suite 
    }
    template = loader.get_template('suites.html')
    return HttpResponse(template.render(context, request))
'''
This function is called by suite_view.html on the initial
page load to render each job into the page

returns: an html page with the jobs rendered in using
django template
'''
def suite_view(request, suitename=''):
    from au import save_json_to_model 
    context = {
        'suite' : suitename
    }
    template = loader.get_template('suite_view.html')
    return HttpResponse(template.render(context, request) )

'''
This function is called by suite_view.html to update the
jobs currently shown on the clients page

returns: a full json of all jobs or
a json that is the difference between
jobs on client side and current jobs 
on server side
'''
def update_view(request, suitename):
    from au import save_json_to_model, get_state_by_id, get_latest_state_id, get_cylc_jobs, get_full_response
    import json
    # get clients last state
    try:
        client_id = int(request.GET.get('client_state'))
        client_jobs = get_state_by_id(client_id)
        data = get_cylc_jobs(suitename)
        import ast 
        from jsondiff import diff
        client_jobs = ast.literal_eval(client_jobs)
        job_diff = diff(client_jobs, data, dump=True)
        return HttpResponse(json.dumps({"id":get_latest_state_id(), "jobs":job_diff, "status":"update"}), content_type='json')
    except Exception as e:
        print(e)
        jobs, child_counts = get_full_response(suitename)
        current_jobs = json.dumps({"id":get_latest_state_id(),"jobs":jobs,"child_counts":child_counts,  "status":"reload"}, indent=4)
        return HttpResponse(current_jobs, content_type='json')
    
    

def start_suite(suitename):
    from suites import is_suite, is_running  
    if is_suite(suitename) and not is_running(suitename):
        print("Started")


def stop_suite(suitename):
    from suite import is_suite, is_running
    if is_suite(suitename) and is_running(suitename):
        print("Stopped")
