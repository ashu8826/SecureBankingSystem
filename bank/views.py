from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from rolepermissions.checkers import has_role
from rolepermissions.roles import assign_role
from django.contrib.auth.models import User


from SecureBankingSystem.roles import *
from bank.models import *
from bank.forms import *
from django.db.models import Q
from datetime import datetime
from django.http import HttpResponse
import os
from os.path import abspath, dirname
import csv
from Crypto.PublicKey import RSA
import random
import string
from random import randint
from django.template import loader, Context
import django
from django.conf import settings
from django.core.mail import send_mail

def AddAccount(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_EMPLOYEE]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == "POST":
            accountNo = request.POST.get('Account')
            accountID = request.POST.get('accountID')
            if 'Open' in request.POST:
                if(isNum(accountNo) and accountNo > 0):
                    try:
                        ao = AccountOpen.objects.get(id=accountID)
                        try:
                            BankAccount.objects.get(AccNo=accountNo)
                            return render(request, 'AddAccount.html', {"Individual": individual, "AccountID": accountID, "Message": "Account already exists!"})
                        except BankAccount.DoesNotExist:
                            bo = BankAccount(AccNo=accountNo, AccType=ao.AccType, User=ao.User, Balance=0, OpenDate=datetime.now(), AccStatus="active")
                            bo.save()
                            ao.delete()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                       Detail='Open - Bank Account: ' + str(bo.AccNo) + ', Balance:' + str(bo.Balance) + ', Type: ' + bo.AccType + ', Open Date: ' + str(bo.OpenDate) + ', Status: ' + bo.AccStatus)
                            l.save()
                            openAccounts = AccountOpen.objects.all()
                            closeAccounts = AccountDelete.objects.all()
                            return render(request, 'AccountAccess.html',
                                      {"Individual": individual, "OpenAccounts": openAccounts,
                                       "CloseAccounts": closeAccounts})
                    except AccountOpen.DoesNotExist:
                        return render(request, 'AddAccount.html', {"Individual": individual, "AccountID": accountID})
                else:
                    return render(request, 'AddAccount.html', {"Individual": individual, "AccountID": accountID})
            else:
                return render(request, 'AddAccount.html', {"Individual": individual, "AccountID": accountID})
        else:
            accountID = request.POST.get('accountID')
            return render(request, 'AddAccount.html', {"Individual": individual, "AccountID": accountID})
    return render(request, 'home.html')

def AccountAccess(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_EMPLOYEE]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == "POST":
            accountNo = request.POST.get('accountID')
            account = BankAccount.objects.get(AccNo=accountNo)
            account.AccStatus = "closed"
            account.save()
            AccountDelete.objects.filter(AccountNo=accountNo).delete()
            l = SystemLogs(CreatedDate=datetime.now(),
                           Detail='Closed - Bank Account: ' + str(account.AccNo) + ', Balance:' + str(account.Balance) + ', Type: ' + account.AccType + ', Open Date: '+ str(account.OpenDate) + ', Status: ' + account.AccStatus)
            l.save()
            openAccounts = AccountOpen.objects.all()
            closeAccounts = AccountDelete.objects.all()
            return render(request, 'AccountAccess.html',
                          {"Individual": individual, "OpenAccounts": openAccounts, "CloseAccounts": closeAccounts})
        else:
            openAccounts = AccountOpen.objects.all()
            closeAccounts = AccountDelete.objects.all()
            return render(request, 'AccountAccess.html',
                          {"Individual": individual, "OpenAccounts": openAccounts, "CloseAccounts": closeAccounts})
    return render(request, 'home.html')

def OpenAccount(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL, ROLE_MERCHANT]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            AccountOpen(User=individual, AccType=request.POST.get('AccountType')).save()
            if has_role(request.user, [ROLE_INDIVIDUAL]):
                return redirect('IndividualHome')
            else:
                return redirect('MerchantHome')
        else:
            individual = ExternalUser.objects.get(Username=request.user.username)
            return render(request, 'OpenAccount.html', {'Individual': individual})
    return render(request, 'home.html')

def CloseAccount(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL, ROLE_MERCHANT]):
        if request.method == "POST":
            AccountDelete(AccountNo=request.POST.get('AccNo')).save()
            if has_role(request.user, [ROLE_INDIVIDUAL]):
                return redirect('IndividualHome')
            else:
                return redirect('MerchantHome')
        else:
            return render(request, 'home.html')
    return render(request, 'home.html')


def AdminHome(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_ADMIN]):
        individual = InternalUser.objects.get(Username=request.user.username)
        tasks = Task.objects.filter(Assignee=individual, Status='notcompleted')
        return render(request, 'AdminHome.html', {"Individual": individual, "Tasks": tasks})
    return render(request, 'home.html')

def Logs(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_ADMIN]):
        individual = InternalUser.objects.get(Username=request.user.username)
        logs = SystemLogs.objects.all()
        return render(request, 'logs.html', {"Individual": individual, "Logs": logs})
    return render(request, 'home.html')

def AddExternalUser(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_ADMIN]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == "POST":

            if 'Add' in request.POST:
                form1 = UserCreationForm(request.POST)
                username = request.POST.get('userNo')
                ua = UserAccess.objects.get(id=username)
                if(form1.is_valid()):
                    form1.save()
                    user = User.objects.get(username=form1.cleaned_data.get('username'))
                    u = ExternalUser(Username=user.username, FirstName=ua.FirstName, LastName=ua.LastName, Email=ua.Email,
                                     Address=ua.Address, City=ua.City, State=ua.State, Zip=ua.Zip, UserType=ua.UserType)
                    RSAkey = RSA.generate(1024)
                    binPrivKey = RSAkey.exportKey()
                    binPubKey = RSAkey.publickey().exportKey()
                    u.PublicKey = binPubKey
                    u.save()
                    loc = abspath(dirname(__file__)) + '\media\_' + u.Username + '_PrivateKey'
                    with open(loc, 'wb+') as pem_out:
                        pem_out.write(binPrivKey)
                    l = SystemLogs(CreatedDate=datetime.now(),
                                   Detail='Added - External User: ' + u.Username + ', First Name:' + u.FirstName + ', Last Name: ' + u.LastName + ', Email: '+ str(u.Email) + ', Address: ' + u.Address + ', City: ' + u.City + ', State: ' + u.State + ', Zip: ' + str(u.Zip) + ', UserType: ' + u.UserType)
                    l.save()
                    if(u.UserType == 'INDIVIDUAL'):
                        assign_role(user, ROLE_INDIVIDUAL)
                    else:
                        assign_role(user, ROLE_MERCHANT)
                    try:
                        send_mail('Bank Account Details', 'Username = ' + user.username + ', Ask Admin ' + u.FirstName + ' ' + u.LastName + ' for the password.',
                              settings.EMAIL_HOST_USER,
                              [u.Email], fail_silently=False)
                    except Exception:
                        print "Sendmail Failed"
                    UserAccess.objects.filter(id=username, UserOperation='add').delete()
                    addUsers = UserAccess.objects.filter(UserOperation='add')
                    modifyUsers = UserAccess.objects.filter(UserOperation='modify')
                    deleteUsers = UserDelete.objects.all()
                    return render(request, 'ExternalUserRequest.html',
                                  {"Individual": individual, "AddUsers": addUsers, "ModifyUsers": modifyUsers,
                                   "DeleteUsers": deleteUsers})
                else:
                    form1 = UserCreationForm()
                    username = request.POST.get('userNo')
                    return render(request, 'AddExternalUser.html',
                                  {"Individual": individual, "Form1": form1, "Username": username})
            else:
                form1 = UserCreationForm()
                username = request.POST.get('userNo')
                return  render(request, 'AddExternalUser.html', {"Individual": individual, "Form1":form1, "Username":username})
        else:
            addUsers = UserAccess.objects.filter(UserOperation='add')
            modifyUsers = UserAccess.objects.filter(UserOperation='modify')
            deleteUsers = UserDelete.objects.all()
            return render(request, 'ExternalUserRequest.html',
                          {"Individual": individual, "AddUsers": addUsers, "ModifyUsers": modifyUsers,
                           "DeleteUsers": deleteUsers})
    return render(request, 'home.html')

def ExternalUserRequest(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_ADMIN]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == "POST":
            if 'Modify' in request.POST:
                username = request.POST.get('userNo')
                u = ExternalUser.objects.get(Username=username)
                ua = UserAccess.objects.get(Username=username)
                u.FirstName = ua.FirstName
                u.LastName = ua.LastName
                u.Email = ua.Email
                u.City = ua.City
                u.Address = ua.Address
                u.State = ua.State
                u.Zip = ua.Zip
                u.save()
                l = SystemLogs(CreatedDate=datetime.now(),
                               Detail='Modified - External User: ' + u.Username + ', First Name:' + u.FirstName + ', Last Name: ' + u.LastName + ', Email: ' + str(u.Email) + ', Address: ' + u.Address + ', City: ' + u.City + ', State: ' + u.State + ', Zip: ' + str(u.Zip) + ', UserType: ' + u.UserType)
                l.save()
                UserAccess.objects.filter(Username=username, UserOperation='modify').delete()
                addUsers = UserAccess.objects.filter(UserOperation='add')
                modifyUsers = UserAccess.objects.filter(UserOperation='modify')
                deleteUsers = UserDelete.objects.all()
                return render(request, 'ExternalUserRequest.html',
                              {"Individual": individual, "AddUsers": addUsers, "ModifyUsers": modifyUsers,
                               "DeleteUsers": deleteUsers})
            else:
                username = request.POST.get('userNo')
                u = ExternalUser.objects.get(Username=username)
                accounts = BankAccount.objects.filter(User=u)
                AccountOpen = BankAccount.objects.filter(User=u).delete()
                for account in accounts:
                    AccountDelete.objects.filter(AccountNo=account.AccNo).delete()
                    account.delete()
                    l = SystemLogs(CreatedDate=datetime.now(),
                                   Detail='Deleted - Bank Account: ' + str(account.AccNo) + ', Balance:' + str(account.Balance) + ', Type: ' + account.AccType + ', Open Date: ' + str(account.OpenDate) + ', Status: ' + account.AccStatus)
                    l.save()
                u.delete()
                User.objects.get(username=username).delete()
                l = SystemLogs(CreatedDate=datetime.now(),
                               Detail='Deleted - External User: ' + u.Username + ', First Name:' + u.FirstName + ', Last Name: ' + u.LastName + ', Email: ' + str(u.Email) + ', Address: ' + u.Address + ', City: ' + u.City + ', State: ' + u.State + ', Zip: ' + str(u.Zip) + ', UserType: ' + u.UserType)
                l.save()
                UserDelete.objects.filter(Username=username).delete()
                addUsers = UserAccess.objects.filter(UserOperation='add')
                modifyUsers = UserAccess.objects.filter(UserOperation='modify')
                deleteUsers = UserDelete.objects.all()
                return render(request, 'ExternalUserRequest.html',
                              {"Individual": individual, "AddUsers": addUsers, "ModifyUsers": modifyUsers,
                               "DeleteUsers": deleteUsers})
        else:
            addUsers = UserAccess.objects.filter(UserOperation='add')
            modifyUsers = UserAccess.objects.filter(UserOperation='modify')
            deleteUsers = UserDelete.objects.all()
            return render(request, 'ExternalUserRequest.html',
                          {"Individual": individual, "AddUsers": addUsers, "ModifyUsers": modifyUsers, "DeleteUsers": deleteUsers})
    return render(request, 'home.html')

def InternalUserLookup(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_ADMIN]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == "POST":
            if 'Save' in request.POST:
                internalUser = InternalUser.objects.get(Username=request.POST.get('EmployeeUsername'))
                internalUserForm = InternalUserForm(request.POST, instance=internalUser)
                if internalUserForm.is_valid():
                    internalUserForm.save()
                    e = InternalUser.objects.get(Username=request.POST.get('EmployeeUsername'))
                    l = SystemLogs(CreatedDate=datetime.now(),
                                   Detail='Modified - Internal User: ' + e.Username + ', First Name:' + e.FirstName + ', Last Name: ' + e.LastName + ', Email: ' + str(e.Email) + ', Address: ' + e.Address + ', City: ' + e.City + ', State: ' + e.State + ', Zip: ' + str(e.Zip) + ', UserType: ' + e.UserType + ', SSN: ' + e.SSN.SSN)
                    l.save()
                    return render(request, 'InternalUserLookup.html',
                                  {"Individual": individual, "AdminRequest": "POST", "InternalUser": internalUser,
                                   "IndividualForm": internalUserForm})
                else:
                    internalUserForm = InternalUserForm(instance=internalUser)
                    return render(request, 'InternalUserLookup.html',
                                  {"Individual": individual, "AdminRequest": "POST", "InternalUser": internalUser,
                                   "IndividualForm": internalUserForm})
            elif 'Delete' in request.POST:
                internalUser = InternalUser.objects.get(Username=request.POST.get('EmployeeUsername'))
                user = User.objects.get(username=internalUser.Username)
                tasks = Task.objects.filter(Assignee=internalUser)
                admin = InternalUser.objects.filter(UserType='ADMIN')
                piiinfo = internalUser.SSN
                piiinfo.delete()
                for task in tasks:
                    adminCount = randint(0, admin.count() - 1)
                    task.Assignee = admin[adminCount]
                    task.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                                   Detail='Updated - Task Detail: ' + str(task.id) + ', Message: ' + task.Message + ', Status: ' + task.Status + ', Assignee: ' + task.Assignee.Username)
                    l.save()
                internalUser.delete()
                user.delete()
                e = InternalUser.objects.get(Username=request.POST.get('EmployeeUsername'))
                l = SystemLogs(CreatedDate=datetime.now(),
                               Detail='Deleted - Internal User: ' + e.Username + ', First Name:' + e.FirstName + ', Last Name: ' + e.LastName + ', Email: ' + str(e.Email) + ', Address: ' + e.Address + ', City: ' + e.City + ', State: ' + e.State + ', Zip: ' + str(e.Zip) + ', UserType: ' + e.UserType + ', SSN: ' + e.SSN.SSN)
                l.save()
                return render(request, 'InternalUserLookup.html', {"Individual": individual, "AdminRequest": "GET", "Message": ""})
            else:
                try:
                    internalUser = InternalUser.objects.get(Username=request.POST.get('EmployeeUsername'))
                    internalUserForm = InternalUserForm(instance=internalUser)
                    return render(request, 'InternalUserLookup.html',
                              {"Individual": individual, "AdminRequest": "POST", "InternalUser": internalUser,  "IndividualForm": internalUserForm})
                except InternalUser.DoesNotExist:
                    return render(request, 'InternalUserLookup.html', {"Individual": individual, "AdminRequest": "GET", "Message": "Invalid username!"})
        else:
            return render(request, 'InternalUserLookup.html', {"Individual": individual, "AdminRequest": "GET", "Message": ""})
    return render(request, 'home.html')

def AddInternalUser(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_ADMIN]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == "POST":
            if 'Add' in request.POST:
                form1 = UserCreationForm(request.POST)
                form2 = PIIInfoForm(request.POST)
                form3 = InternalUserForm(request.POST)
                if(form1.is_valid() == False):
                    form1 = UserCreationForm()
                    return render(request, 'AddInternalUser.html',
                                  {"Individual": individual, "Form1": form1, "Form2": form2, "Form3": form3})
                if (form2.is_valid() == False):
                    form2 = PIIInfoForm(request.POST)
                    return render(request, 'AddInternalUser.html',
                                  {"Individual": individual, "Form1": form1, "Form2": form2, "Form3": form3})
                if(form1.is_valid() and form2.is_valid() and form3.is_valid()):
                    form1.save()
                    form2.save()
                    user = User.objects.get(username=form1.cleaned_data.get('username'))
                    p = PIIInfo.objects.get(SSN=form2.data.get('SSN'))
                    e = InternalUser(Username=user.username, FirstName=form3.data.get('FirstName'), LastName=form3.data.get('LastName'),
                                     Email=form3.data.get('Email'), Address=form3.data.get('Address'), City=form3.data.get('City'),
                                     State=form3.data.get('State'), Zip=form3.data.get('Zip'), SSN=p, PIIAccess=0)
                    e.UserType = request.POST.get('UserType')
                    e.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                                   Detail='Added - Internal User: ' + e.Username + ', First Name:' + e.FirstName + ', Last Name: ' + e.LastName + ', Email: ' + str(e.Email) + ', Address: ' + e.Address + ', City: ' + e.City  + ', State: ' + e.State  + ', Zip: ' + str(e.Zip)  + ', UserType: ' + e.UserType + ', SSN: ' + e.SSN.SSN)
                    l.save()
                    if(e.UserType == 'ADMIN'):
                        assign_role(user, ROLE_ADMIN)
                    elif(e.UserType == 'MANAGER'):
                        assign_role(user, ROLE_MANAGER)
                    else:
                        assign_role(user, ROLE_EMPLOYEE)
                    try:
                        send_mail('Bank Account Details', 'Username = ' + user.username + ', Ask Admin ' + e.FirstName + ' ' + e.LastName + ' for the password.',
                              settings.EMAIL_HOST_USER,
                              [e.Email], fail_silently=False)
                    except Exception:
                        print "Sendmail Failed"
                    return render(request, 'InternalUserLookup.html',
                                  {"Individual": individual, "AdminRequest": "GET", "Message": ""})
                else:
                    form1 = UserCreationForm()
                    form2 = PIIInfoForm()
                    form3 = InternalUserForm()
                    return render(request, 'AddInternalUser.html',
                                  {"Individual": individual, "Form1": form1, "Form2": form2, "Form3": form3})
            else:
                form1 = UserCreationForm()
                form2 = PIIInfoForm()
                form3 = InternalUserForm()
                return  render(request, 'AddInternalUser.html', {"Individual": individual, "Form1":form1, "Form2":form2, "Form3":form3})

        else:
            return render(request, 'InternalUserLookup.html',
                          {"Individual": individual, "AdminRequest": "GET", "Message": ""})
    return render(request, 'home.html')

def PII(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_ADMIN]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == "POST":
            if individual.PIIAccess == 1:
                try:
                    ssn = PIIInfo.objects.get(SSN=request.POST.get('inputSSN'))
                    return render(request, 'PII.html',
                          {"Individual": individual, "AdminRequest": "POST", "SSN": ssn})
                except PIIInfo.DoesNotExist:
                    return render(request, 'PII.html', {"Individual": individual, "AdminRequest": "GET", "Message": "Invalid SSN!"})
            else:
                return render(request, 'PII.html',
                              {"Individual": individual, "AdminRequest": "GET", "Message": "You do not have PII Access!"})
        else:
            return render(request, 'PII.html', {"Individual": individual, "AdminRequest": "GET", "Message": ""})
    return render(request, 'home.html')

def ManagerHome(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_MANAGER]):
        individual = InternalUser.objects.get(Username=request.user.username)
        tasks = Task.objects.filter(Assignee=individual, Status='notcompleted')
        return render(request, 'ManagerHome.html', {"Individual": individual, "Tasks": tasks})
    return render(request, 'home.html')

def EmployeeHome(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_EMPLOYEE]):
        individual = InternalUser.objects.get(Username=request.user.username)
        tasks = Task.objects.filter(Assignee=individual, Status='notcompleted')
        return render(request, 'EmployeeHome.html', {"Individual": individual, "Tasks": tasks})
    return render(request, 'home.html')

def TransactionLookup(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_MANAGER, ROLE_EMPLOYEE]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == "POST":
            try:
                transaction = Transaction.objects.get(id=request.POST.get('TransactionID'))
                return render(request, 'TransactionLookup.html',
                          {"Individual": individual, "AdminRequest": "POST", "Transaction": transaction})
            except Transaction.DoesNotExist:
                return render(request, 'TransactionLookup.html', {"Individual": individual, "AdminRequest": "GET", "Message": "Invalid Transaction ID!"})
        else:
            return render(request, 'TransactionLookup.html', {"Individual": individual, "AdminRequest": "GET", "Message": ""})
    return render(request, 'home.html')

def TAuthorize(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_MANAGER, ROLE_EMPLOYEE]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == "POST":
            transaction = Transaction.objects.get(id=request.POST.get('TransID'))
            try:
                sendAccount = BankAccount.objects.get(AccNo=transaction.SendAcc)
                recvAccount = BankAccount.objects.get(AccNo=transaction.RecAcc)
                if sendAccount.AccStatus == "active" and recvAccount.AccStatus == "active":
                    if transaction.TransType == "credit":
                        recvAccount.Balance = float(sendAccount.Balance) + float(transaction.Amount)
                        recvAccount.save()
                        transaction.TransStatus = "approved"
                        transaction.save()
                        l = SystemLogs(CreatedDate=datetime.now(),
                                       Detail='Updated - Transaction Type: ' + transaction.TransType + ', Amount:' + str(
                                           transaction.Amount) + ', Status: ' + transaction.TransType + ', Send Account: ' + str(
                                           transaction.SendAcc) + ', Received Account: ' + str(transaction.RecAcc))
                        l.save()
                        l = SystemLogs(CreatedDate=datetime.now(),
                                       Detail='Updated - ' + str(transaction.Amount) + ' credited to account ' + str(recvAccount.AccNo))
                        l.save()
                    elif transaction.TransType == "debit":
                        if float(recvAccount.Balance) >= float(transaction.Amount):
                            sendAccount.Balance = float(recvAccount.Balance) - float(transaction.Amount)
                            sendAccount.save()
                            transaction.TransStatus = "approved"
                            transaction.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                           Detail='Updated - Transaction Type: ' + transaction.TransType + ', Amount:' + str(
                                               transaction.Amount) + ', Status: ' + transaction.TransType + ', Send Account: ' + str(
                                               transaction.SendAcc) + ', Received Account: ' + str(transaction.RecAcc))
                            l.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                           Detail='Updated - ' + str(transaction.Amount) + ' debited from account ' + str(
                                               sendAccount.AccNo))
                            l.save()
                        else:
                            transaction.TransStatus = "declined"
                            transaction.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                           Detail='Updated - Transaction Type: ' + transaction.TransType + ', Amount:' + str(
                                               transaction.Amount) + ', Status: ' + transaction.TransType + ', Send Account: ' + str(
                                               transaction.SendAcc) + ', Received Account: ' + str(transaction.RecAcc))
                            l.save()
                            return render(request, 'TransactionLookup.html',
                                          {"Individual": individual, "AdminRequest": "POST", "Transaction": transaction,
                                           "Message2": "Transaction Declined"})
                    else:
                        if float(sendAccount.Balance) >= float(transaction.Amount):
                            sendAccount.Balance = float(sendAccount.Balance) - float(transaction.Amount)
                            sendAccount.save()
                            recvAccount.Balance = float(recvAccount.Balance) + float(transaction.Amount)
                            recvAccount.save()
                            transaction.TransStatus = "approved"
                            transaction.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                           Detail='Updated - Transaction Type: ' + transaction.TransType + ', Amount:' + str(
                                               transaction.Amount) + ', Status: ' + transaction.TransType + ', Send Account: ' + str(
                                               transaction.SendAcc) + ', Received Account: ' + str(transaction.RecAcc))
                            l.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                           Detail='Updated - ' + str(transaction.Amount) + ' deducted from account ' + str(
                                               sendAccount.AccNo))
                            l.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                           Detail='Updated - ' + str(transaction.Amount) + ' added in account ' + str(
                                               recvAccount.AccNo))
                            l.save()
                        else:
                            transaction.TransStatus = "declined"
                            transaction.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                           Detail='Updated - Transaction Type: ' + transaction.TransType + ', Amount:' + str(
                                               transaction.Amount) + ', Status: ' + transaction.TransType + ', Send Account: ' + str(
                                               transaction.SendAcc) + ', Received Account: ' + str(transaction.RecAcc))
                            l.save()
                            return render(request, 'TransactionLookup.html',
                                          {"Individual": individual, "AdminRequest": "POST", "Transaction": transaction,
                                           "Message2": "Transaction Declined"})
                    if has_role(request.user, [ROLE_MANAGER]):
                        return redirect('ManagerHome')
                    else:
                        return redirect('EmployeeHome')
                else:
                    transaction.TransStatus = "declined"
                    transaction.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                                   Detail='Updated - Transaction Type: ' + transaction.TransType + ', Amount:' + str(
                                       Transaction.Amount) + ', Status: ' + transaction.TransType + ', Send Account: ' + str(
                                       transaction.SendAcc) + ', Received Account: ' + str(transaction.RecAcc))
                    l.save()
                    return render(request, 'TransactionLookup.html',
                                  {"Individual": individual, "AdminRequest": "POST", "Transaction": transaction,
                                   "Message2": "Transaction Declined"})
            except BankAccount.DoesNotExist:
                transaction.TransStatus = "declined"
                transaction.save()
                l = SystemLogs(CreatedDate=datetime.now(),
                               Detail='Updated - Transaction Type: ' + transaction.TransType + ', Amount:' + str(
                                   Transaction.Amount) + ', Status: ' + transaction.TransType + ', Send Account: ' + str(
                                   transaction.SendAcc) + ', Received Account: ' + str(transaction.RecAcc))
                l.save()
                return render(request, 'TransactionLookup.html',
                              {"Individual": individual, "AdminRequest": "POST", "Transaction": transaction,
                               "Message2": "Transaction Declined"})
            return render(request, 'TransactionLookup.html',
                          {"Individual": individual, "AdminRequest": "POST", "Transaction": transaction})
        else:
            return render(request, 'TransactionLookup.html', {"Individual": individual, "AdminRequest": "GET", "Message": ""})
    return render(request, 'home.html')

def TModify(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_MANAGER, ROLE_EMPLOYEE]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == "POST":
            transaction = Transaction.objects.get(id=request.POST.get('TransID'))
            amount = request.POST.get('TAmount')
            if(isNum(amount) and float(amount) > 0):
                transaction.Amount = float(amount)
                transaction.save()
                l = SystemLogs(CreatedDate=datetime.now(),
                               Detail='Modified - Transaction Type: ' + transaction.TransType + ', Amount:' + str(
                                   amount) + ', Status: ' + transaction.TransType + ', Send Account: ' + str(
                                   transaction.SendAcc) + ', Received Account: ' + str(transaction.RecAcc))
                l.save()
                if has_role(request.user, [ROLE_MANAGER]):
                    return redirect('ManagerHome')
                else:
                    return redirect('EmployeeHome')
            else:
                return render(request, 'TransactionLookup.html',
                          {"Individual": individual, "AdminRequest": "POST", "Transaction": transaction, "Message1": "Amount should be valid number greater than 0"})
        else:
            return render(request, 'TransactionLookup.html', {"Individual": individual, "AdminRequest": "GET", "Message": ""})
    return render(request, 'home.html')

def TCancel(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_MANAGER, ROLE_EMPLOYEE]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == "POST":
            transaction = Transaction.objects.get(id=request.POST.get('TransID'))
            try:
                task = Task.objects.get(TaskDetail=transaction)
                task.delete()
                l = SystemLogs(CreatedDate=datetime.now(),
                               Detail='Deleted - Task Detail: ' + str(task.id) + ', Message: ' + task.Message + ', Status: ' + task.Status + ', Assignee: ' + task.Assignee.Username)
                l.save()
            except Task.DoesNotExist:
                return render(request, 'TransactionLookup.html',
                              {"Individual": individual, "AdminRequest": "POST", "Transaction": transaction,
                               "Message2": "Cannot cancel cleared transactions"})
            if transaction.TransStatus == "pending" or transaction.TransStatus == "processing":
                transaction.delete()
                l = SystemLogs(CreatedDate=datetime.now(),
                               Detail='Deleted - Transaction Type: ' + transaction.TransType + ', Amount:' + str(
                                   transaction.Amount) + ', Status: ' + transaction.TransType + ', Send Account: ' + str(
                                   transaction.SendAcc) + ', Received Account: ' + str(transaction.RecAcc))
                l.save()
                if has_role(request.user, [ROLE_MANAGER]):
                    return redirect('ManagerHome')
                else:
                    return redirect('EmployeeHome')
            else:
                return render(request, 'TransactionLookup.html',
                              {"Individual": individual, "AdminRequest": "POST", "Transaction": transaction,
                               "Message2": "Cannot cancel approved or declined transactions"})
        else:
            return render(request, 'TransactionLookup.html', {"Individual": individual, "AdminRequest": "GET", "Message": ""})
    return render(request, 'home.html')

def TransactionInquiry(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_MANAGER, ROLE_EMPLOYEE]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == "POST":
            if isNum(request.POST.get('AccNo')):
                try:
                    account = BankAccount.objects.get(AccNo=request.POST.get('AccNo'))
                    transactions = Transaction.objects.filter(Q(SendAcc=account.AccNo) | Q(RecAcc=account.AccNo))
                    return render(request, 'TransactionInquiry.html',
                              {"Individual": individual, "AdminRequest": "POST", "Transactions": transactions})
                except BankAccount.DoesNotExist:
                    return render(request, 'TransactionInquiry.html', {"Individual": individual, "AdminRequest": "GET", "Message": "Invalid Account!"})
            else:
                return render(request, 'TransactionInquiry.html',
                              {"Individual": individual, "AdminRequest": "GET", "Message": "Invalid Account!"})
        else:
            return render(request, 'TransactionInquiry.html', {"Individual": individual, "AdminRequest": "GET", "Message": ""})
    return render(request, 'home.html')

def CompleteTask(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE]):
        if request.method == "POST":
            task = Task.objects.get(id=request.POST.get('TaskId'))
            task.Status = "completed"
            task.save()
            l = SystemLogs(CreatedDate=datetime.now(),
                     Detail='Updated - Task Detail: ' + str(task.id) + ', Message: ' + task.Message + ', Status: ' + task.Status)
            l.save()
            if has_role(request.user, [ROLE_ADMIN]):
                return redirect('AdminHome')
            elif has_role(request.user, [ROLE_MANAGER]):
                return redirect('ManagerHome')
            else:
                return redirect('EmployeeHome')
        return render(request, 'home.html')
    return render(request, 'home.html')

def ExternalUserAccess(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == "POST":
            if 'Delete' in request.POST:
                try:
                    externalUser = ExternalUser.objects.get(Username=request.POST.get('EmployeeUsername'))
                    userDelete = UserDelete(Username=externalUser.Username)
                    userDelete.save()
                    if has_role(request.user, [ROLE_ADMIN]):
                        return redirect('AdminHome')
                    elif has_role(request.user, [ROLE_MANAGER]):
                        return redirect('ManagerHome')
                    else:
                        return redirect('EmployeeHome')
                except ExternalUser.DoesNotExist:
                    form1 = UserAccessForm()
                    return render(request, 'ExternalUserLookup.html',
                                  {"Individual": individual, "Message": "", "Form1": form1,  "Message": "Invalid Username"})
            else:
                form1 = UserAccessForm(request.POST)
                if form1.is_valid():
                    ua = UserAccess(Username="add", FirstName=form1.data.get('FirstName'),
                                    LastName=form1.data.get('LastName'),
                                    Email=form1.data.get('Email'),
                                    Address=form1.data.get('Address'),
                                    City=form1.data.get('City'),
                                    State=form1.data.get('State'), Zip=form1.data.get('Zip'))
                    ua.UserType = request.POST.get('UserType')
                    ua.UserOperation = "add"
                    ua.save()
                    if has_role(request.user, [ROLE_ADMIN]):
                        return redirect('AdminHome')
                    elif has_role(request.user, [ROLE_MANAGER]):
                        return redirect('ManagerHome')
                    else:
                        return redirect('EmployeeHome')
                form1 = UserAccessForm()
                return render(request, 'ExternalUserLookup.html',
                              {"Individual": individual, "Message": "", "Form1": form1})
        else:
            form1 = UserAccessForm()
            return render(request, 'ExternalUserLookup.html',
                          {"Individual": individual, "Message": "", "Form1": form1})
    return render(request, 'home.html')

def EditInfo(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == 'POST':
            internalUserForm = InternalUserForm(request.POST, instance=individual)
            if internalUserForm.is_valid():
                internalUserForm.save()
                return render(request, 'EmployeeInfo.html',
                              {"Individual": individual, "IndividualForm": internalUserForm})
        internalUserForm = InternalUserForm(instance=individual)
        return render(request, 'EmployeeInfo.html',
                      {"Individual": individual, "IndividualForm": internalUserForm})
    return render(request, 'home.html')

def MerchantHome(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_MERCHANT]):
        individual = ExternalUser.objects.get(Username=request.user.username)
        accounts = BankAccount.objects.filter(User=individual)
        return render(request, 'IndividualHome.html', {"Individual": individual, "Accounts": accounts})
    return render(request, 'home.html')

def IndividualHome(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL]):
        individual = ExternalUser.objects.get(Username=request.user.username)
        accounts = BankAccount.objects.filter(User=individual)
        return render(request, 'IndividualHome.html', {"Individual":individual, "Accounts":accounts})
    return render(request, 'home.html')

def IndividualInfo(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL, ROLE_MERCHANT]):
        individual = ExternalUser.objects.get(Username=request.user.username)
        if request.method == 'POST':
            externalUserForm = ExternalUserForm(request.POST, instance=individual)
            if externalUserForm.is_valid():
                ua = UserAccess(Username=individual.Username, FirstName=externalUserForm.data.get('FirstName'), LastName=externalUserForm.data.get('LastName'),
                                     Email=externalUserForm.data.get('Email'), Address=externalUserForm.data.get('Address'), City=externalUserForm.data.get('City'),
                                     State=externalUserForm.data.get('State'), Zip=externalUserForm.data.get('Zip'))
                ua.UserType = individual.UserType
                ua.UserOperation = "modify"
                ua.save()
                if has_role(request.user, [ROLE_INDIVIDUAL]):
                    return redirect('IndividualHome')
                else:
                    return redirect('MerchantHome')
        externalUserForm = ExternalUserForm(instance=individual)
        return render(request, 'PersonalInformation.html', {"Individual":individual, "IndividualForm":externalUserForm})
    return render(request, 'home.html')

def IndividualAccount(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL, ROLE_MERCHANT]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            transactions = Transaction.objects.filter(Q(SendAcc=account.AccNo) | Q(RecAcc=account.AccNo))
            return render(request, 'Account.html', {"Individual": individual, "Account": account, "Transactions": transactions})
        return render(request, 'home.html')
    return render(request, 'home.html')

def isNum(data):
    try:
        float(data)
        return True
    except ValueError:
        return False

def Debit(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL, ROLE_MERCHANT]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            allowed_chars = ''.join((string.digits))
            plainText = ''.join(random.choice(allowed_chars) for _ in range(6))
            try:
                send_mail('Bank Account OTP',
                          'OTP = ' + plainText,
                          settings.EMAIL_HOST_USER,
                          [individual.Email], fail_silently=False)
            except Exception:
                print "Sendmail Failed"
            return render(request, 'debit.html', {"Individual": individual, "Account": account, "Message": "", "OTPCode": plainText})
        return render(request, 'home.html')
    return render(request, 'home.html')

def doDebit(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL, ROLE_MERCHANT]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            data = request.POST.get('Amount')
            if(isNum(data) and float(data) > 0 and float(account.Balance) >= float(data)):
                if(float(data) > 500):
                    if int(request.POST.get('OtpCodeH')) == int(request.POST.get('OtpCode')):
                        t = Transaction(TransDate=datetime.now(), TransType='debit', Amount=float(data),
                                    TransStatus='pending',
                                    SendAcc=account.AccNo, RecAcc=account.AccNo)
                        t.save()
                        task = Task(TaskDetail=t, Message='general', Status='notcompleted')
                        employees = InternalUser.objects.filter(UserType='EMPLOYEE')
                        managers = InternalUser.objects.filter(UserType='MANAGER')
                        admin = InternalUser.objects.filter(UserType='ADMIN')
                        if(float(data) > 10000):
                            if managers:
                                managerCount = randint(0, managers.count()-1)
                                task.Assignee = managers[managerCount]
                                task.save()
                            else:
                                adminCount = randint(0, admin.count() - 1)
                                task.Assignee = admin[adminCount]
                                task.save()
                        else:
                            if employees:
                                employeeCount = randint(0, employees.count() - 1)
                                task.Assignee = employees[employeeCount]
                                task.save()
                            elif managers:
                                managerCount = randint(0, managers.count()-1)
                                task.Assignee = managers[managerCount]
                                task.save()
                            else:
                                adminCount = randint(0, admin.count() - 1)
                                task.Assignee = admin[adminCount]
                                task.save()
                        l = SystemLogs(CreatedDate=datetime.now(),
                                   Detail='Added - Transaction Type: ' + t.TransType + ', Amount:' + str(
                                       data) + ', Status: ' + t.TransType + ', Send Account: ' + str(
                                       t.SendAcc) + ', Received Account: ' + str(t.RecAcc))
                        l.save()
                        l = SystemLogs(CreatedDate=datetime.now(),
                                   Detail='Added - Task Detail: ' + str(task.id) + ', Message: ' + task.Message + ', Status: ' + task.Status + ', Assignee: ' + task.Assignee.Username)
                        l.save()
                        if has_role(request.user, [ROLE_INDIVIDUAL]):
                            return redirect('IndividualHome')
                        else:
                            return redirect('MerchantHome')
                    else:
                        allowed_chars = ''.join((string.digits))
                        plainText = ''.join(random.choice(allowed_chars) for _ in range(6))
                        try:
                            send_mail('Bank Account OTP',
                                      'OTP = ' + plainText,
                                      settings.EMAIL_HOST_USER,
                                      [individual.Email], fail_silently=False)
                        except Exception:
                            print "Sendmail Failed"
                        return render(request, 'debit.html', {"Individual": individual, "Account": account,
                                                              "Message": "OTP Authentication Failed", "OTPCode": plainText})
                else:
                    t = Transaction(TransDate=datetime.now(), TransType='debit', Amount=float(data),
                                    TransStatus='cleared', SendAcc=account.AccNo, RecAcc=account.AccNo)
                    t.save()
                    account.Balance = float(account.Balance) - float(data)
                    account.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                                   Detail='Added - Transaction Type: ' + t.TransType + ', Amount:' + str(
                                       data) + ', Status: ' + t.TransType + ', Send Account: ' + str(
                                       t.SendAcc) + ', Received Account: ' + str(t.RecAcc))
                    l.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                                   Detail='Updated - ' + str(data) + ' deducted from account ' + str(account.AccNo))
                    l.save()
                    if has_role(request.user, [ROLE_INDIVIDUAL]):
                        return redirect('IndividualHome')
                    else:
                        return redirect('MerchantHome')
            else:
                allowed_chars = ''.join((string.digits))
                plainText = ''.join(random.choice(allowed_chars) for _ in range(6))
                try:
                    send_mail('Bank Account OTP',
                              'OTP = ' + plainText,
                              settings.EMAIL_HOST_USER,
                              [individual.Email], fail_silently=False)
                except Exception:
                    print "Sendmail Failed"
                return render(request, 'debit.html', {"Individual": individual, "Account": account, "Message": "Amount should be valid number between 0 and balance in account", "OTPCode": plainText})
        return render(request, 'home.html')
    return render(request, 'home.html')

def Credit(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL, ROLE_MERCHANT]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            return render(request, 'credit.html', {"Individual": individual, "Account": account, "Message": ""})
        return render(request, 'home.html')
    return render(request, 'home.html')

def doCredit(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL, ROLE_MERCHANT]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            data = request.POST.get('Amount')
            if (isNum(data) and float(data) > 0):
                if float(data) > 500:
                    t = Transaction(TransDate=datetime.now(), TransType='credit', Amount=float(data),
                                    TransStatus='pending',
                                    SendAcc=account.AccNo, RecAcc=account.AccNo)
                    t.save()
                    task = Task(TaskDetail=t, Message='general', Status='notcompleted')
                    employees = InternalUser.objects.filter(UserType='EMPLOYEE')
                    managers = InternalUser.objects.filter(UserType='MANAGER')
                    admin = InternalUser.objects.filter(UserType='ADMIN')
                    if (float(data) > 10000):
                        if managers:
                            managerCount = randint(0, managers.count() - 1)
                            task.Assignee = managers[managerCount]
                            task.save()
                        else:
                            adminCount = randint(0, admin.count() - 1)
                            task.Assignee = admin[adminCount]
                            task.save()
                    else:
                        if employees:
                            employeeCount = randint(0, employees.count() - 1)
                            task.Assignee = employees[employeeCount]
                            task.save()
                        elif managers:
                            managerCount = randint(0, managers.count() - 1)
                            task.Assignee = managers[managerCount]
                            task.save()
                        else:
                            adminCount = randint(0, admin.count() - 1)
                            task.Assignee = admin[adminCount]
                            task.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                                   Detail='Added - Transaction Type: ' + t.TransType + ', Amount:' + str(
                                       data) + ', Status: ' + t.TransType + ', Send Account: ' + str(
                                       t.SendAcc) + ', Received Account: ' + str(t.RecAcc))
                    l.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                                   Detail='Added - Task Detail: ' + str(task.id) + ', Message: ' + task.Message + ', Status: ' + task.Status + ', Assignee: ' + task.Assignee.Username)
                    l.save()
                    if has_role(request.user, [ROLE_INDIVIDUAL]):
                        return redirect('IndividualHome')
                    else:
                        return redirect('MerchantHome')
                else:
                    t = Transaction(TransDate=datetime.now(), TransType='credit', Amount=float(data),
                                    TransStatus='cleared',
                                    SendAcc=account.AccNo, RecAcc=account.AccNo)
                    t.save()
                    account.Balance = float(account.Balance) + float(data)
                    account.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                                   Detail='Added - Transaction Type: ' + t.TransType + ', Amount:' + str(
                                       data) + ', Status: ' + t.TransType + ', Send Account: ' + str(
                                       t.SendAcc) + ', Received Account: ' + str(t.RecAcc))
                    l.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                                   Detail='Updated - ' + str(data) + ' credited to account ' + str(account.AccNo))
                    l.save()
                    if has_role(request.user, [ROLE_INDIVIDUAL]):
                        return redirect('IndividualHome')
                    else:
                        return redirect('MerchantHome')
            else:
                return render(request, 'credit.html', {"Individual": individual, "Account": account,
                                                       "Message": "Amount should be valid number greater than 0"})
        return render(request, 'home.html')
    return render(request, 'home.html')

def Transfer(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL, ROLE_MERCHANT]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            return render(request, 'transfer.html', {"Individual": individual, "Account": account, "Message": ""})
        return render(request, 'home.html')
    return render(request, 'home.html')

def doTransfer(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL, ROLE_MERCHANT]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            toAccount = BankAccount.objects.get(AccNo=request.POST.get('ToAccount'))
            if not toAccount:
                return render(request, 'transfer.html', {"Individual": individual, "Account": account,
                                                         "Message": "Account to transfer is not valid"})
            if account.AccNo == toAccount.AccNo:
                return render(request, 'transfer.html', {"Individual": individual, "Account": account,
                                                         "Message": "From and to accounts cannot be the same"})
            data = request.POST.get('Amount')
            if (isNum(data) and float(data) > 0 and float(account.Balance) >= float(data)):
                if float(data) > 500:
                    if request.FILES['PrivateKeyFileLoc']:
                        binPrivKey = request.FILES['PrivateKeyFileLoc'].read()
                        allowed_chars = ''.join((string.ascii_letters, string.digits))
                        plainText = ''.join(random.choice(allowed_chars) for _ in range(32))
                        privKeyObj = RSA.importKey(binPrivKey)
                        pubKeyObj = RSA.importKey(individual.PublicKey)
                        enc_data = pubKeyObj.encrypt(plainText, 32)
                        dec_data = privKeyObj.decrypt(enc_data)
                        if dec_data == plainText:
                            t = Transaction(TransDate=datetime.now(), TransType='transfer', Amount=float(data),
                                            TransStatus='pending',
                                            SendAcc=account.AccNo, RecAcc=toAccount.AccNo)
                            t.save()
                            task = Task(TaskDetail=t, Message='general', Status='notcompleted')
                            employees = InternalUser.objects.filter(UserType='EMPLOYEE')
                            managers = InternalUser.objects.filter(UserType='MANAGER')
                            admin = InternalUser.objects.filter(UserType='ADMIN')
                            if (float(data) > 10000):
                                if managers:
                                    managerCount = randint(0, managers.count() - 1)
                                    task.Assignee = managers[managerCount]
                                    task.save()
                                else:
                                    adminCount = randint(0, admin.count() - 1)
                                    task.Assignee = admin[adminCount]
                                    task.save()
                            else:
                                if employees:
                                    employeeCount = randint(0, employees.count() - 1)
                                    task.Assignee = employees[employeeCount]
                                    task.save()
                                elif managers:
                                    managerCount = randint(0, managers.count() - 1)
                                    task.Assignee = managers[managerCount]
                                    task.save()
                                else:
                                    adminCount = randint(0, admin.count() - 1)
                                    task.Assignee = admin[adminCount]
                                    task.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                           Detail='Added - Transaction Type: ' + t.TransType + ', Amount:' + str(
                                               data) + ', Status: ' + t.TransType + ', Send Account: ' + str(
                                               t.SendAcc) + ', Received Account: ' + str(t.RecAcc))
                            l.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                           Detail='Added - Task Detail: ' + str(task.id) + ', Message: ' + task.Message + ', Status: ' + task.Status + ', Assignee: ' + task.Assignee.Username)
                            l.save()
                            if has_role(request.user, [ROLE_INDIVIDUAL]):
                                return redirect('IndividualHome')
                            else:
                                return redirect('MerchantHome')
                        else:
                            return render(request, 'transfer.html', {"Individual": individual, "Account": account,
                                                                     "Message": "Private key authentication failed!"})

                    else:
                        return render(request, 'transfer.html', {"Individual": individual, "Account": account,
                                                                 "Message": "Private Key must be provided for transactions more than 500"})
                else:
                    t = Transaction(TransDate=datetime.now(), TransType='transfer', Amount=float(data), TransStatus='cleared',
                                    SendAcc=account.AccNo, RecAcc=toAccount.AccNo)
                    t.save()
                    account.Balance = float(account.Balance) - float(data)
                    account.save()
                    toAccount.Balance = float(toAccount.Balance) + float(data)
                    toAccount.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                             Detail='Transaction Type: ' + t.TransType + ', Amount:' + str(data) + ', Status: ' + t.TransType + ', Send Account: ' + str(t.SendAcc) + ', Received Account: ' + str(t.RecAcc))
                    l.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                             Detail='' + str(data) + ' deducted from account ' + str(account.AccNo))
                    l.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                             Detail='' + str(data) + ' added in account ' + str(toAccount.AccNo))
                    l.save()
                    if has_role(request.user, [ROLE_INDIVIDUAL]):
                        return redirect('IndividualHome')
                    else:
                        return redirect('MerchantHome')
            else:
                return render(request, 'transfer.html', {"Individual": individual, "Account": account,
                                                       "Message": "Amount should be valid number between 0 and balance in account"})
        return render(request, 'home.html')
    return render(request, 'home.html')

def Payment(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL, ROLE_MERCHANT]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            merchants = ExternalUser.objects.filter(UserType='MERCHANT')
            return render(request, 'payment.html', {"Individual": individual, "Account": account, "Merchants":merchants, "Message": ""})
        return render(request, 'home.html')
    return render(request, 'home.html')

def doPayment(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL, ROLE_MERCHANT]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            try:
                merchant = ExternalUser.objects.get(Username=request.POST.get('organization'))
            except ExternalUser.DoesNotExist:
                return render(request, 'payment.html', {"Individual": individual, "Account": account,
                                                         "Message": "Merchant is not selected"})
            toAccount = BankAccount.objects.filter(Q(User=merchant, AccType='Savings') | Q(User=merchant, AccType='Checking')).first()
            if not toAccount:
                return render(request, 'payment.html', {"Individual": individual, "Account": account,
                                                         "Message": "Merchant selected does not have a valid checing or savings account"})
            if account.AccNo == toAccount.AccNo:
                return render(request, 'payment.html', {"Individual": individual, "Account": account,
                                                         "Message": "From and to accounts cannot be the same"})
            data = request.POST.get('Amount')
            if (isNum(data) and float(data) > 0 and float(account.Balance) >= float(data)):
                if float(data) > 500:
                    if request.FILES['PrivateKeyFileLoc']:
                        binPrivKey = request.FILES['PrivateKeyFileLoc'].read()
                        allowed_chars = ''.join((string.ascii_letters, string.digits))
                        plainText = ''.join(random.choice(allowed_chars) for _ in range(32))
                        privKeyObj = RSA.importKey(binPrivKey)
                        pubKeyObj = RSA.importKey(individual.PublicKey)
                        enc_data = pubKeyObj.encrypt(plainText, 32)
                        dec_data = privKeyObj.decrypt(enc_data)
                        if dec_data == plainText:
                            t = Transaction(TransDate=datetime.now(), TransType='payment', Amount=float(data),
                                            TransStatus='pending',
                                            SendAcc=account.AccNo, RecAcc=toAccount.AccNo)
                            t.save()
                            task = Task(TaskDetail=t, Message='general', Status='notcompleted')
                            employees = InternalUser.objects.filter(UserType='EMPLOYEE')
                            managers = InternalUser.objects.filter(UserType='MANAGER')
                            admin = InternalUser.objects.filter(UserType='ADMIN')
                            if (float(data) > 10000):
                                if managers:
                                    managerCount = randint(0, managers.count() - 1)
                                    task.Assignee = managers[managerCount]
                                    task.save()
                                else:
                                    adminCount = randint(0, admin.count() - 1)
                                    task.Assignee = admin[adminCount]
                                    task.save()
                            else:
                                if employees:
                                    employeeCount = randint(0, employees.count() - 1)
                                    task.Assignee = employees[employeeCount]
                                    task.save()
                                elif managers:
                                    managerCount = randint(0, managers.count() - 1)
                                    task.Assignee = managers[managerCount]
                                    task.save()
                                else:
                                    adminCount = randint(0, admin.count() - 1)
                                    task.Assignee = admin[adminCount]
                                    task.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                           Detail='Added - Transaction Type: ' + t.TransType + ', Amount:' + str(
                                               data) + ', Status: ' + t.TransType + ', Send Account: ' + str(
                                               t.SendAcc) + ', Received Account: ' + str(t.RecAcc))
                            l.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                           Detail='Added - Task Detail: ' + str(task.id) + ', Message: ' + task.Message + ', Status: ' + task.Status + ', Assignee: ' + task.Assignee.Username)
                            l.save()
                            if has_role(request.user, [ROLE_INDIVIDUAL]):
                                return redirect('IndividualHome')
                            else:
                                return redirect('MerchantHome')
                        else:
                            return render(request, 'payment.html', {"Individual": individual, "Account": account,
                                                                     "Message": "Private key authentication failed!"})

                    else:
                        return render(request, 'payment.html', {"Individual": individual, "Account": account,
                                                                 "Message": "Private Key must be provided for transactions more than 500"})
                else:
                    t = Transaction(TransDate=datetime.now(), TransType='payment', Amount=float(data), TransStatus='cleared',
                                    SendAcc=account.AccNo, RecAcc=toAccount.AccNo)
                    t.save()
                    account.Balance = float(account.Balance) - float(data)
                    account.save()
                    toAccount.Balance = float(toAccount.Balance) + float(data)
                    toAccount.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                             Detail='Transaction Type: ' + t.TransType + ', Amount:' + str(data) + ', Status: ' + t.TransType + ', Send Account: ' + str(t.SendAcc) + ', Received Account: ' + str(t.RecAcc))
                    l.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                             Detail='' + str(data) + ' deducted from account ' + str(account.AccNo))
                    l.save()
                    l = SystemLogs(CreatedDate=datetime.now(),
                             Detail='' + str(data) + ' added in account ' + str(toAccount.AccNo))
                    l.save()
                    if has_role(request.user, [ROLE_INDIVIDUAL]):
                        return redirect('IndividualHome')
                    else:
                        return redirect('MerchantHome')
            else:
                return render(request, 'payment.html', {"Individual": individual, "Account": account,
                                                       "Message": "Amount should be valid number between 0 and balance in account"})
        return render(request, 'home.html')
    return render(request, 'home.html')


def Downloadpage(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL, ROLE_MERCHANT]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            transactions = Transaction.objects.filter(Q(SendAcc=account.AccNo) | Q(RecAcc=account.AccNo))

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=%s' % 'Statement.csv'
            writer = csv.writer(response)
            for transaction in transactions:
                row = ""
                for field in Transaction._meta.fields:
                    row += str(getattr(transaction, field.name)) + ","
                writer.writerow(row)
            return response
        return render(request, 'home.html')
    return render(request, 'home.html')

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