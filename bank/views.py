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
from Crypto import Random


def AdminHome(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_ADMIN]):
        return render(request, 'AdminHome.html')
    return render(request, 'home.html')

def ManagerHome(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_MANAGER]):
        return render(request, 'ManagerHome.html')
    return render(request, 'home.html')

def EmployeeHome(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_EMPLOYEE]):
        return render(request, 'EmployeeHome.html')
    return render(request, 'home.html')

def MerchantHome(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_MERCHANT]):
        return render(request, 'MerchantHome.html')
    return render(request, 'home.html')

def IndividualHome(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL]):
        individual = ExternalUser.objects.get(Username=request.user.username)
        accounts = BankAccount.objects.filter(User=individual)
        return render(request, 'IndividualHome.html', {"Individual":individual, "Accounts":accounts})
    return render(request, 'home.html')

def IndividualInfo(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL]):
        individual = ExternalUser.objects.get(Username=request.user.username)
        return render(request, 'PersonalInformation.html', {"Individual":individual})
    return render(request, 'home.html')

def IndividualAccount(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL]):
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
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            return render(request, 'debit.html', {"Individual": individual, "Account": account, "Message": ""})
        return render(request, 'home.html')
    return render(request, 'home.html')

def doDebit(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            data = request.POST.get('Amount')
            if(isNum(data) and float(data) > 0 and float(account.Balance) >= float(data)):
                t = Transaction(TransDate=datetime.now(), TransType='debit', Amount=float(data), TransStatus='cleared', SendAcc=account.AccNo, RecAcc=account.AccNo)
                t.save()
                account.Balance = float(account.Balance) - float(data)
                account.save()
                return redirect('IndividualHome')
            else:
                return render(request, 'debit.html', {"Individual": individual, "Account": account, "Message": "Amount should be valid number between 0 and balance in account"})
        return render(request, 'home.html')
    return render(request, 'home.html')

def Credit(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            return render(request, 'credit.html', {"Individual": individual, "Account": account, "Message": ""})
        return render(request, 'home.html')
    return render(request, 'home.html')

def doCredit(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL]):
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
                return redirect('IndividualHome')
            else:
                return render(request, 'credit.html', {"Individual": individual, "Account": account,
                                                       "Message": "Amount should be valid number greater than 0"})
        return render(request, 'home.html')
    return render(request, 'home.html')

def Transfer(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            return render(request, 'transfer.html', {"Individual": individual, "Account": account, "Message": ""})
        return render(request, 'home.html')
    return render(request, 'home.html')

def doTransfer(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL]):
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
                        loc = abspath(dirname(__file__))+'\media\_'+individual.Username+'_privateKey'
                        with open(loc, 'wb+') as destination:
                            f = request.FILES['PrivateKeyFileLoc']
                            for chunk in f.chunks():
                                destination.write(chunk)
                        with open(loc, 'rb') as pem_in:
                            binPrivKey = pem_in.read()

                        plainText = 'abcdefgh'
                        privKeyObj = RSA.importKey(binPrivKey)
                        pubKeyObj = RSA.importKey(individual.publicKey)
                        enc_data = pubKeyObj.encrypt(plainText, 32)
                        dec_data = privKeyObj.decrypt(enc_data)
                        if dec_data == plainText:
                            print "True"

                else:
                    t = Transaction(TransDate=datetime.now(), TransType='transfer', Amount=float(data), TransStatus='cleared',
                                    SendAcc=toAccount.AccNo, RecAcc=account.AccNo)
                    t.save()
                    account.Balance = float(account.Balance) - float(data)
                    account.save()
                    toAccount.Balance = float(toAccount.Balance) + float(data)
                    toAccount.save()
                    return redirect('IndividualHome')
            else:
                return render(request, 'transfer.html', {"Individual": individual, "Account": account,
                                                       "Message": "Amount should be valid number between 0 and balance in account"})
        return render(request, 'home.html')
    return render(request, 'home.html')

def Payment(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL]):
        if request.method == "POST":
            individual = ExternalUser.objects.get(Username=request.user.username)
            account = BankAccount.objects.get(User=individual, AccNo=request.POST.get('AccNo'))
            return render(request, 'payment.html', {"Individual": individual, "Account": account})
        return render(request, 'home.html')
    return render(request, 'home.html')

def Downloadpage(request):
    if request.user.is_authenticated() and has_role(request.user, [ROLE_INDIVIDUAL]):
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
    binPrivKey = RSAkey.exportKey('DER')
    binPubKey = RSAkey.publickey().exportKey('DER')
    # user.publicKey = binPubKey
    loc = abspath(dirname(__file__)) + '\media\_'+'user.username'+'_sysPrivateKey'
    with open(loc, 'wb+') as pem_out:
        pem_out.write(binPrivKey)

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