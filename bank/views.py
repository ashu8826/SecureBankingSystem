from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from rolepermissions.checkers import has_role
from SecureBankingSystem.roles import *

def AdminHome(request):
    return render(request, 'AdminHome.html')

def ManagerHome(request):
    return render(request, 'ManagerHome.html')

def EmployeeHome(request):
    return render(request, 'EmployeeHome.html')

def MerchantHome(request):
    return render(request, 'MerchantHome.html')

def IndividualHome(request):
    return render(request, 'IndividualHome.html')

def home(request):
     if request.user.is_authenticated():
        if has_role(request.user, [ROLE_ADMIN]):
            return redirect('AdminHome')
        elif has_role(request.user, [ROLE_MANAGER]):
            return redirect('ManagerHome')
        elif has_role(request.user, [ROLE_EMPLOYEE]):
            return redirect('EmployeeHome')
        elif has_role(request.user, [ROLE_MERCHANT]):
            return redirect('MerchantHome')
        elif has_role(request.user, [ROLE_INDIVIDUAL]):
            return redirect('IndividualHome')
     return render(request, 'home.html')


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})