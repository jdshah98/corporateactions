from django.http import JsonResponse
from .models import Holding, Transaction
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from .serializers import TransactionSerializer, HoldingSerializer
from django.db.models import Sum


class StockException(Exception):
    def __init__(self, msg, *args: object):
        super().__init__(*args)
        self.msg = msg
        
    def __str__(self):
        return self.msg


@api_view(['GET'])
def get_transactions(request, company_name):
    transactions = Transaction.objects.filter(company_name=company_name)
    if transactions.count() > 0:
        transaction_serializer = TransactionSerializer(transactions, many=True)
        return JsonResponse(transaction_serializer.data, safe=False)
    else:
        return JsonResponse(data=f"No Transactions Found for company: {company_name}", safe=False)


@api_view(['GET'])
def get_holdings(request, company_name):
    holding = Holding.objects.filter(company_name=company_name).last()
    if holding is not None:
        holding_serializer = HoldingSerializer(holding)
        return JsonResponse(holding_serializer.data, safe=False)
    else:
        return JsonResponse(data=f"No Holding Found for company: {company_name}", safe=False)


@api_view(['POST'])
def create_transaction(request):
    try:
        transaction_data = JSONParser().parse(request)
        if transaction_data["trade_type"]=='BUY' or transaction_data["trade_type"]=='SELL':
            transaction_data["amount"] = transaction_data["qty"] * transaction_data["buy_price"]
            base_info = {
                'qty': 0,
                'buy_price': 0,
                'cummulative_allocation': 0,
                'bal_qty': 0,
                'avg_buy_price': 0
            }
            
            transactions = Transaction.objects.filter(company_name=transaction_data["company_name"])
            split_transaction = transactions.filter(trade_type="SPLIT").last()
            if split_transaction is not None:
                transactions = transactions.filter(id__gt=split_transaction.id)
                base_info['qty'] = split_transaction.qty
                base_info['buy_price'] = split_transaction.avg_buy_price
                base_info['cummulative_allocation'] = split_transaction.cummulative_allocation
                base_info['bal_qty'] = split_transaction.bal_qty
                base_info['avg_buy_price'] = split_transaction.avg_buy_price

            buy_qty = transactions.filter(trade_type='BUY').aggregate(count=Sum('qty'))['count']
            total_buy_qty = base_info['qty'] + (buy_qty if buy_qty is not None else 0)
            sell_qty = transactions.filter(trade_type="SELL").aggregate(count=Sum('qty'))['count']
            total_sell_qty = sell_qty if sell_qty is not None else 0
            
            if transaction_data["trade_type"]=="BUY":
                total_buy_qty += transaction_data["qty"]
            else:
                total_sell_qty += transaction_data["qty"]
            closing_qty = total_buy_qty - total_sell_qty
            if closing_qty < 0:
                raise StockException("Available Stock Qty is Less")
            lot_pending = base_info['qty'] - total_sell_qty
            
            transactions_history = {'qty': [], 'buy_price': [], 'lot_pending_qty': [], 'lot_value': []}
            if lot_pending > 0:
                transactions_history['qty'].append(base_info['qty'])
                transactions_history['buy_price'].append(base_info['buy_price'])
                transactions_history['lot_pending_qty'].append(lot_pending)
                transactions_history['lot_value'].append(lot_pending * base_info['buy_price'])
            
            transaction_serializer = TransactionSerializer(transactions, many=True)
            transaction_lst = list(map(lambda x: dict(x), transaction_serializer.data))
            transaction_lst.append(transaction_data)
            
            for transaction in transaction_lst:
                transactions_history['qty'].append(transaction['qty'])
                transactions_history['buy_price'].append(transaction['buy_price'])
                if transaction['trade_type'] == "BUY":
                    lot_pending = lot_pending + transaction['qty']
                    if lot_pending > 0:
                        pending_qty = min(lot_pending, transaction['qty'])
                        transactions_history['lot_pending_qty'].append(pending_qty)
                        transactions_history['lot_value'].append(pending_qty * transaction['buy_price'])
                    else:
                        transactions_history['lot_pending_qty'].append(0)
                        transactions_history['lot_value'].append(0)
                else:
                    transactions_history['lot_pending_qty'].append(0)
                    transactions_history['lot_value'].append(0)

            transaction_data['cummulative_allocation'] = sum(transactions_history['lot_value'])
            transaction_data['bal_qty'] = closing_qty
            transaction_data['avg_buy_price'] = (transaction_data['cummulative_allocation'] / closing_qty) if closing_qty > 0 else 0
            transaction_serializer = TransactionSerializer(data = transaction_data)
                
            if transaction_serializer.is_valid():
                holding_data = {
                    'company_name': transaction_data['company_name'],
                    'qty': transaction_data['bal_qty'],
                    'avg_buy_price': transaction_data['avg_buy_price'],
                    'amount_invested': transaction_data['bal_qty'] * transaction_data["avg_buy_price"],
                    'cmp': transaction_data['buy_price'],
                    'current_value': transaction_data["bal_qty"] * transaction_data["buy_price"]
                }
                holding_serializer = HoldingSerializer(data = holding_data)
                if holding_serializer.is_valid():
                    transaction_serializer.save()
                    holding_serializer.save()
                    return JsonResponse(data={'transaction': transaction_serializer.data, 'holding': holding_serializer.data}, safe=False)
                else:
                    return JsonResponse(data="Invalid Holding", safe=False)
            else:
                return JsonResponse(data="Invalid Transaction", safe=False)
        elif transaction_data["trade_type"]=='SPLIT':
            last_transaction = Transaction.objects.filter(company_name=transaction_data["company_name"]).last()
            if last_transaction is not None:
                transaction_data["buy_price"] = (last_transaction.buy_price * last_transaction.bal_qty) / transaction_data["qty"]
                transaction_data["amount"] = transaction_data["qty"] * transaction_data["buy_price"]
                transaction_data["cummulative_allocation"] = last_transaction.cummulative_allocation
                transaction_data["bal_qty"] = transaction_data["qty"]
                transaction_data["avg_buy_price"] = transaction_data["cummulative_allocation"] / transaction_data["qty"]
                                
                transaction_serializer = TransactionSerializer(data=transaction_data)
                
                if transaction_serializer.is_valid():
                    holding_data = {
                        'company_name': transaction_data["company_name"],
                        'qty': transaction_data["bal_qty"],
                        'avg_buy_price': transaction_data["avg_buy_price"],
                        'amount_invested': transaction_data["bal_qty"] * transaction_data["avg_buy_price"],
                        'cmp': transaction_data["buy_price"],
                        'current_value': transaction_data["bal_qty"] * transaction_data["buy_price"]
                    }
                    holding_serializer = HoldingSerializer(data=holding_data)
                    if holding_serializer.is_valid():
                        transaction_serializer.save()
                        holding_serializer.save()
                        return JsonResponse(data={'transaction': transaction_serializer.data, 'holding': holding_serializer.data}, safe=False)
                    else:
                        return JsonResponse(data="Invalid Holding", safe=False)
                else:
                    return JsonResponse(data="Invalid Transaction", safe=False)
            else:
                return JsonResponse(data=f"No Stocks Found for company: {transaction_data['company_name']}", safe=False)
    except StockException as e:
        return JsonResponse(data=e.msg, safe=False)
