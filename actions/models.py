from django.db import models


# Create your models here.
class Transaction(models.Model):
    date = models.DateField()
    company_name = models.CharField(max_length=50)
    trade_type = models.CharField(max_length=10)
    qty = models.IntegerField()
    buy_price = models.FloatField()
    amount = models.FloatField()
    cummulative_allocation = models.FloatField()
    bal_qty = models.IntegerField()
    avg_buy_price = models.FloatField()
    
    def __str__(self):
        d = {
            'date': self.date,
            'company_name': self.company_name,
            'trade_type': self.trade_type,
            'qty': self.qty,
            'buy_price': self.buy_price,
            'amount': self.amount,
            'cummulative_allocation': self.cummulative_allocation,
            'bal_qty': self.bal_qty,
            'avg_buy_price': self.avg_buy_price
        }
        return str(d)


class Holding(models.Model):
    company_name = models.CharField(max_length=50)
    qty = models.IntegerField()
    avg_buy_price = models.FloatField()
    amount_invested = models.FloatField()
    cmp = models.FloatField()
    current_value = models.FloatField()
    
    def __str__(self):
        d = {
            'company_name': self.company_name,
            'qty': self.qty,
            'avg_buy_price': self.avg_buy_price,
            'amount_invested': self.amount_invested,
            'cmp': self.cmp,
            'current_value': self.current_value
        }
        return str(d)
