# from django.shortcuts import render
import datetime
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Holding, Transaction
from django.db.models import Sum

def prepare_new_transaction(transactions, new_transaction):
    total_buy_qty = Transaction.objects.filter(trade_type="BUY").aggregate(Sum('qty'))['qty__sum']
    if total_buy_qty is None:
        total_buy_qty = 0
    total_sell_qty = Transaction.objects.filter(trade_type="SELL").aggregate(Sum('qty'))['qty__sum']
    if total_sell_qty is None:
        total_sell_qty = 0
    if new_transaction.trade_type=="BUY":
        total_buy_qty += new_transaction.qty
    else:
        total_sell_qty += new_transaction.qty
    print("Buy Qty:", total_buy_qty)
    print("Sell Qty:", total_sell_qty)
    closing_qty = total_buy_qty - total_sell_qty
    lot_pending = -total_sell_qty
    print("Lot pending:", lot_pending)
    transaction_dict = {'qty': [], 'buy_price': [], 'lot_pending_qty': [], 'lot_value': []}
    for transaction in list(transactions) + [new_transaction]:
        transaction_dict['qty'].append(transaction.qty)
        transaction_dict['buy_price'].append(transaction.buy_price)
        if transaction.trade_type=="BUY":
            lot_pending = lot_pending + transaction.qty
            if lot_pending > 0:
                final_pending = min(lot_pending, transaction.qty)
                transaction_dict['lot_pending_qty'].append(final_pending)
                transaction_dict['lot_value'].append(final_pending*transaction.buy_price)
            else:
                transaction_dict['lot_pending_qty'].append(0)            
                transaction_dict['lot_value'].append(0)
        else:
            transaction_dict['lot_pending_qty'].append(0)
            transaction_dict['lot_value'].append(0)
    print(transaction_dict)
    new_transaction.cummulative_allocation = sum(transaction_dict['lot_value'])
    new_transaction.bal_qty = closing_qty
    new_transaction.avg_buy_price = new_transaction.cummulative_allocation / closing_qty
    print(new_transaction)
    return new_transaction

# Create your views here.
@csrf_exempt
def add_transaction(request):
    body_data = json.loads(request.body)
    
    company_name = body_data["company_name"]
    print(company_name)
    trade_type = body_data["trade_type"]
    print(trade_type)
    qty = body_data["qty"]
    print(qty)
    
    if trade_type=="BUY" or trade_type=="SELL":
        buy_price = body_data["buy_price"]
        print(buy_price)
        amount = qty * buy_price
        print(amount)

        transactions = list(Transaction.objects.all())
        
        new_transaction = Transaction()
        new_transaction.date = datetime.date.today()
        new_transaction.company_name = company_name
        new_transaction.trade_type = trade_type
        new_transaction.qty = qty
        new_transaction.buy_price = buy_price
        new_transaction.amount = amount
        
        for transaction in transactions:
            print(transaction)
        
        # print(new_transaction)
        
        new_transaction = prepare_new_transaction(transactions, new_transaction)
        new_transaction.save()
        # new_transaction = transactions[-1]
        
        holding = Holding()
        holding.company_name = company_name
        holding.qty = new_transaction.bal_qty
        holding.avg_buy_price = new_transaction.avg_buy_price
        holding.amount_invested = holding.qty * holding.avg_buy_price
        holding.cmp = new_transaction.buy_price
        holding.current_value = holding.qty * holding.cmp
        print(holding)
        holding.save()
    elif trade_type=="SPLIT":
        transactions = list(Transaction.objects.all())
        print(transactions[-1])
        new_transaction = Transaction()
        new_transaction.date = datetime.date.today()
        new_transaction.company_name = company_name        
        new_transaction.trade_type = trade_type
        new_transaction.qty = qty
        new_transaction.cummulative_allocation = transactions[-1].cummulative_allocation
        new_transaction.bal_qty = qty
        new_transaction.avg_buy_price = new_transaction.cummulative_allocation / qty
        print(new_transaction)
    
    return HttpResponse("Hello")
    