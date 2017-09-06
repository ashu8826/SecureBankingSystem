from django.http import HttpResponse

def index(request):
    return HttpResponse("This is the Homepage")

def login(request):
    return HttpResponse("This is the Login page")
