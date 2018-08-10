from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    url(r'^$', views.register, name='register'),
    url(r'^register', views.register, name='register'),
    url(r'^suites/', views.suites, name='suites'),
    url(r'^suite_view/(?P<suitename>[^/]+)/', views.suite_view, name='suite_view'),
    url(r'^update_view/(?P<suitename>[^/]+)/', views.update_view , name='update_view'),
    url(r'^start/(?P<suitename>[^/]+)/', views.start_suite, name='start_suite'),
    url(r'^stop/(?P<suitename>[^/]+)/', views.stop_suite, name='stop_suite'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)#this is for dev, should be changed for production
