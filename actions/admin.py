from django.contrib import admin
from .models import Transaction, Holding

# Register your models here.
admin.site.register(Transaction)
admin.site.register(Holding)
