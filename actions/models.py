from django.db import models


# Create your models here.
class Transaction(models.Model):
    date = models.DateField(auto_now_add=True)
    company_name = models.CharField(max_length=50)
    trade_type = models.CharField(max_length=10)
    qty = models.IntegerField()
    buy_price = models.FloatField()
    amount = models.FloatField()
    cummulative_allocation = models.FloatField()
    bal_qty = models.IntegerField()
    avg_buy_price = models.FloatField()


class Holding(models.Model):
    company_name = models.CharField(max_length=50)
    qty = models.IntegerField()
    avg_buy_price = models.FloatField()
    amount_invested = models.FloatField()
    cmp = models.FloatField()
    current_value = models.FloatField()
