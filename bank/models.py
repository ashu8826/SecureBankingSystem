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
    PublicKey = models.TextField()

class PIIInfo(models.Model):
    SSN = models.TextField(primary_key=True)
    VisaStatus = models.CharField(max_length=200)

class InternalUser(models.Model):
    Username = models.CharField(max_length = 50)
    FirstName = models.CharField(max_length = 50)
    LastName = models.CharField(max_length = 50)
    Email = models.EmailField()
    Address = models.CharField(max_length = 200)
    City = models.CharField(max_length = 20)
    State = models.CharField(max_length = 20)
    Zip = models.IntegerField()
    SSN = models.ForeignKey(PIIInfo)
    UserType = models.CharField(max_length=50)
    AccessPrivilege = models.CharField(max_length=30, default='RE1')
    PIIAccess = models.IntegerField()

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

class Task(models.Model):
    TaskDetail = models.ForeignKey(Transaction)
    Message = models.CharField(max_length = 200)
    Status = models.CharField(max_length = 50)
    Assignee = models.ForeignKey(InternalUser, null=True)

class SystemLogs(models.Model):
    CreatedDate = models.DateField()
    Detail = models.TextField()