# from django.shortcuts import render
import datetime
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Holding, Transaction
from django.db.models import Sum

def prepare_new_transaction(transactions, new_transaction, base_info):
    total_buy_qty =  base_info['qty'] + sum(map(lambda t: t.qty, filter(lambda t: t.trade_type=="BUY", transactions)))
    if total_buy_qty is None:
        total_buy_qty = 0
    total_sell_qty = sum(map(lambda t: t.qty, filter(lambda t: t.trade_type=="SELL", transactions)))
    if total_sell_qty is None:
        total_sell_qty = 0
    if new_transaction.trade_type=="BUY":
        total_buy_qty += new_transaction.qty
    else:
        total_sell_qty += new_transaction.qty
    print("Buy Qty:", total_buy_qty)
    print("Sell Qty:", total_sell_qty)
    closing_qty = total_buy_qty - total_sell_qty
    lot_pending = base_info['qty']-total_sell_qty
    print("Lot pending:", lot_pending)
    transaction_dict = {'qty': [], 'buy_price': [], 'lot_pending_qty': [], 'lot_value': []}
    if lot_pending>0:
        transaction_dict['qty'].append(base_info['qty'])
        transaction_dict['buy_price'].append(base_info['buy_price'])
        transaction_dict['lot_pending_qty'].append(lot_pending)
        transaction_dict['lot_value'].append(lot_pending * base_info['buy_price'])
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
        
        base_info = {
            'qty': 0,
            'buy_price': 0,
            'cummulative_allocation': 0,
            'bal_qty': 0,
            'avg_buy_price': 0
        }
        
        transactions = list(Transaction.objects.filter(company_name=company_name))
        split_transactions = list(filter(lambda t: t.trade_type=="SPLIT", transactions))
        if len(split_transactions)>0:
            base_transaction = split_transactions[-1]
            transactions = list(filter(lambda t:t.id > base_transaction.id, transactions))
            base_info['qty'] = base_transaction.qty
            base_info['buy_price'] = base_transaction.avg_buy_price
            base_info['cummulative_allocation'] = base_transaction.cummulative_allocation
            base_info['bal_qty'] = base_transaction.bal_qty
            base_info['avg_buy_price'] = base_transaction.avg_buy_price
                    
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
        
        new_transaction = prepare_new_transaction(transactions, new_transaction, base_info)
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
        latest_transaction = Transaction.objects.filter(company_name=company_name).last()
        
        new_transaction = Transaction()
        new_transaction.date = datetime.date.today()
        new_transaction.company_name = company_name        
        new_transaction.trade_type = trade_type
        new_transaction.qty = qty
        new_transaction.buy_price = (latest_transaction.buy_price * latest_transaction.qty) / qty
        new_transaction.amount = new_transaction.qty * new_transaction.buy_price
        new_transaction.cummulative_allocation = latest_transaction.cummulative_allocation
        new_transaction.bal_qty = qty
        new_transaction.avg_buy_price = new_transaction.cummulative_allocation / qty
        print(new_transaction)
        
        new_transaction.save()
    
        holding = Holding()
        holding.company_name = company_name
        holding.qty = new_transaction.bal_qty
        holding.avg_buy_price = new_transaction.avg_buy_price
        holding.amount_invested = holding.qty * holding.avg_buy_price
        holding.cmp = new_transaction.buy_price
        holding.current_value = holding.qty * holding.cmp
    
        print(holding)
        holding.save()
    
    return HttpResponse("Hello")
    