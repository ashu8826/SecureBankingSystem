from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView
from . import views

urlpatterns = [
    url(r'^AdminHome/$',views.AdminHome, name='AdminHome'),
    url(r'^ManagerHome/$',views.ManagerHome, name='ManagerHome'),
    url(r'^EmployeeHome/$',views.EmployeeHome, name='EmployeeHome'),
    url(r'^MerchantHome/$',views.MerchantHome, name='MerchantHome'),
    url(r'^IndividualHome/$',views.IndividualHome, name='IndividualHome'),
    url(r'^$', views.home, name='home'),
    #url(r'^$', TemplateView.as_view(template_name='home.html'), name='home'),
    url(r'^login/$', auth_views.login, {'template_name': 'login.html'}, name='login'),
    #url(r'^signup/$', views.signup, name='signup'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'logged_out.html'}, name='logout'),
]