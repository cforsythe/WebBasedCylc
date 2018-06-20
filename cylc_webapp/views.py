# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.template import loader

import os

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

from au import get_response, cylc_run_dir, get_jobs_from_response
from job import Job

def register(request):
    template = loader.get_template('register.html')
    return HttpResponse(template.render())

def suites(request):
    dirs_with_suite = list()
    dirs = os.listdir(cylc_run_dir())
    for direc in dirs:
        path = os.path.join(cylc_run_dir(),direc, "suite.rc")
        if os.path.isfile(path):
            dirs_with_suite.append(direc)
    context = {
        "suites": dirs_with_suite 
    }
    template = loader.get_template('suites.html')
    return HttpResponse(template.render(context, request))
    
def suite_view(request, suitename=''):
    from au import save_json_to_model
    data = get_response(suitename)
    if(data is None):
        template = loader.get_template('suite_view.html')
        return HttpResponse(template.render(request) )
    else:
        current_jobs = get_jobs_from_response(data)
        save_json_to_model(current_jobs)
        context = {
            'data' : current_jobs,
            'suite' : suitename
        }
        template = loader.get_template('suite_view.html')
        return HttpResponse(template.render(context, request) )

def update_view(request, suitename):
    from au import diff_state, save_json_to_model, get_state_by_id, get_latest_state_id
    data = get_response(suitename)
    if data is None:
        template = loader.get_template('suite_view.html')
        return HttpResponse(template.render(request))
    else:
        # get clients last state
        client_id = int(request.GET.get('client_state'))
        # loads latest data from cylc
        current_jobs = get_jobs_from_response(data)
        save_json_to_model(current_jobs)
        # check if website has received a previous state from server

        # try to get state if it exists, otherwise return all data
        try:
            full_state = get_state_by_id(client_id)
        except:
            import json
            current_jobs = json.dumps({"id":get_latest_state_id(),"jobs":current_jobs}, indent=4)
            return HttpResponse(current_jobs, content_type='application/json')
        
        client_jobs = get_jobs_from_response(full_state)
        print(diff_state(client_jobs, current_jobs))

        
    print("HASHVAL: " + request.GET.get('client_state'))

