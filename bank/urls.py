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
    url(r'^IndividualHome/Info$',views.IndividualInfo, name='IndividualInfo'),
    url(r'^IndividualHome/Debit$',views.Debit, name='Debit'),
    url(r'^IndividualHome/Credit$',views.Credit, name='Credit'),
    url(r'^IndividualHome/Transfer$',views.Transfer, name='Transfer'),
    url(r'^IndividualHome/Payment$', views.Payment, name='Payment'),
    url(r'^IndividualHome/Downloadpage',views.Downloadpage, name='Downloadpage'),
    url(r'^IndividualHome/Account$',views.IndividualAccount, name='Account'),
    url(r'^IndividualHome/doDebit$',views.doDebit, name='doDebit'),
    url(r'^IndividualHome/doCredit$',views.doCredit, name='doCredit'),
    url(r'^IndividualHome/doTransfer$',views.doTransfer, name='doTransfer'),

    url(r'^$', views.home, name='home'),
    url(r'^login/$', auth_views.login, {'template_name': 'login.html'}, name='login'),
    #url(r'^signup/$', views.signup, name='signup'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'logged_out.html'}, name='logout'),
]