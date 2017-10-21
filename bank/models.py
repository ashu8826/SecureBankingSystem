# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class ExternalUser(models.Model):
    Username = models.CharField(max_length = 50)
    FirstName = models.CharField(max_length = 50)
    LastName = models.CharField(max_length = 50)
    Email = models.EmailField()
    Address = models.CharField(max_length = 200)
    City = models.CharField(max_length = 20)
    State = models.CharField(max_length = 20)
    Zip = models.IntegerField()
    UserType = models.CharField(max_length = 50)

class BankAccount(models.Model):
    AccNo = models.IntegerField()
    Balance = models.FloatField()
    AccType = models.CharField(max_length = 60)
    OpenDate = models.DateField()
    User = models.ForeignKey(ExternalUser)
    AccStatus = models.CharField(max_length = 30)

class Transaction(models.Model):
    TransDate = models.DateField()
    TransType = models.CharField(max_length = 20)
    Amount = models.FloatField()
    TransStatus = models.CharField(max_length = 20)
    SendAcc = models.IntegerField()
    RecAcc = models.IntegerField()
