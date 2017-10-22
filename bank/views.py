from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from rolepermissions.checkers import has_role

from SecureBankingSystem.roles import *
from bank.models import *
from django.db.models import Q
from datetime import datetime
import os
from os.path import abspath, dirname
from Crypto.PublicKey import RSA
import random
import string

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

def InternalUserLookup(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_ADMIN]):
        individual = InternalUser.objects.get(Username=request.user.username)
        if request.method == "POST":
            try:
                internalUser = InternalUser.objects.get(Username=request.POST.get('EmployeeUsername'))
                return render(request, 'InternalUserLookup.html',
                          {"Individual": individual, "AdminRequest": "POST", "InternalUser": internalUser})
            except InternalUser.DoesNotExist:
                return render(request, 'InternalUserLookup.html', {"Individual": individual, "AdminRequest": "GET", "Message": "Invalid username!"})
        else:
            return render(request, 'InternalUserLookup.html', {"Individual": individual, "AdminRequest": "GET", "Message": ""})
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

def CompleteTask(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE]):
        if request.method == "POST":
            task = Task.objects.get(id=request.POST.get('TaskId'))
            task.Status = "completed"
            task.save()
            l = SystemLogs(CreatedDate=datetime.now(),
                     Detail='Updated - Task Detail: ' + task.TaskDetail + ', Message: ' + task.Message + ', Status: ' + task.Status)
            l.save()
            if has_role(request.user, [ROLE_ADMIN]):
                return redirect('AdminHome')
            elif has_role(request.user, [ROLE_MANAGER]):
                return redirect('ManagerHome')
            else:
                return redirect('EmployeeHome')
        return render(request, 'home.html')
    return render(request, 'home.html')

def EditInfo(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE]):
        individual = InternalUser.objects.get(Username=request.user.username)
        return render(request, 'EmployeeInfo.html', {"Individual":individual})
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
        return render(request, 'PersonalInformation.html', {"Individual":individual})
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
            return render(request, 'debit.html', {"Individual": individual, "Account": account, "Message": ""})
        return render(request, 'home.html')
    return render(request, 'home.html')

def doDebit(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL, ROLE_MERCHANT]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            data = request.POST.get('Amount')
            if(isNum(data) and float(data) > 0 and float(account.Balance) >= float(data)):
                t = Transaction(TransDate=datetime.now(), TransType='debit', Amount=float(data), TransStatus='cleared', SendAcc=account.AccNo, RecAcc=account.AccNo)
                t.save()
                account.Balance = float(account.Balance) - float(data)
                account.save()
                l = SystemLogs(CreatedDate=datetime.now(),
                         Detail='Added - Transaction Type: ' + t.TransType + ', Amount:' + str(data) + ', Status: ' + t.TransType + ', Send Account: ' + str(t.SendAcc) + ', Received Account: ' + str(t.RecAcc))
                l.save()
                l = SystemLogs(CreatedDate=datetime.now(),
                         Detail='Updated - '+str(data)+' deducted from account '+str(account.AccNo))
                l.save()
                if has_role(request.user, [ROLE_INDIVIDUAL]):
                    return redirect('IndividualHome')
                else:
                    return redirect('MerchantHome')
            else:
                return render(request, 'debit.html', {"Individual": individual, "Account": account, "Message": "Amount should be valid number between 0 and balance in account"})
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
                t = Transaction(TransDate=datetime.now(), TransType='credit', Amount=float(data), TransStatus='cleared',
                                SendAcc=account.AccNo, RecAcc=account.AccNo)
                t.save()
                account.Balance = float(account.Balance) + float(data)
                account.save()
                l = SystemLogs(CreatedDate=datetime.now(),
                         Detail='Added - Transaction Type: ' + t.TransType + ', Amount:' + str(data) + ', Status: ' + t.TransType + ', Send Account: ' + str(t.SendAcc) + ', Received Account: ' + str(t.RecAcc))
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
                                            TransStatus='processing',
                                            SendAcc=account.AccNo, RecAcc=toAccount.AccNo)
                            t.save()
                            task = Task(TaskDetail=t, Message='general', Status='notcompleted')
                            task.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                     Detail='Added - Transaction Type: ' + t.TransType + ', Amount:' + str(data) + ', Status: ' + t.TransType + ', Send Account: ' + str(t.SendAcc) + ', Received Account: ' + str(t.RecAcc))
                            l.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                     Detail='Added - Task Detail: '+task.TaskDetail+', Message: '+task.Message+', Status: '+task.Status)
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
                                            TransStatus='processing',
                                            SendAcc=account.AccNo, RecAcc=toAccount.AccNo)
                            t.save()
                            task = Task(TaskDetail=t, Message='general', Status='notcompleted')
                            task.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                     Detail='Added - Transaction Type: ' + t.TransType + ', Amount:' + str(data) + ', Status: ' + t.TransType + ', Send Account: ' + str(t.SendAcc) + ', Received Account: ' + str(t.RecAcc))
                            l.save()
                            l = SystemLogs(CreatedDate=datetime.now(),
                                     Detail='Added - Task Detail: ' + task.TaskDetail + ', Message: ' + task.Message + ', Status: ' + task.Status)
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
            return render(request, 'download.html', {"Individual": individual, "Account": account})
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

def whileCreateUser():
    RSAkey = RSA.generate(1024)
    binPrivKey = RSAkey.exportKey()
    binPubKey = RSAkey.publickey().exportKey()
    # user.PublicKey = binPubKey
    # user.save()
    #loc = abspath(dirname(__file__)) + '\media\_'+user.Username+'_PrivateKey'
    #with open(loc, 'wb+') as pem_out:
     #   pem_out.write(binPrivKey)

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