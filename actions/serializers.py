from rest_framework import serializers
from .models import Transaction, Holding


class TransactionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Transaction
        fields = ('company_name', 'trade_type', 'qty', 
                  'buy_price', 'amount', 
                  'cummulative_allocation', 'bal_qty', 'avg_buy_price')
      
        
class HoldingSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Holding
        fields = ('company_name', 'qty', 'avg_buy_price',
                  'amount_invested', 'cmp', 'current_value')
