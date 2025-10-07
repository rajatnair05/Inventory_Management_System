from django.shortcuts import render, redirect, get_object_or_404
import json
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
import datetime
import mysql.connector
from zoneinfo import ZoneInfo
import requests
from .models import StockItems,StockLedgerLineItems,StockLedger,SuppUser
from django.utils import timezone
import pytz
from django.db import transaction

API_BASE_URL = "http://api.elxer.com/v2/elxerone/agent-list"  
API_TOKEN = "36A9F18467C3EFD17E223FA46A3E4"  



def login(request):  
    return render(request, 'login.html') 



def signup(request):
    return render(request, 'signup.html')



def dashboard(request):
    return render(request, 'dashboard.html') 



def stocks(req):
    employees = find_employee()
    return render(req, "stocks.html", {"employees": employees})



def Employee_stock_detail(req, emp_id):
    
    employee = find_employee(emp_id)

    stockdata = (
        StockLedgerLineItems.objects
        .select_related('doc', 'user', 'product_item')
        .filter(user__employee_id=emp_id)
        .values(
            'product_item_id',
            'product_item__product',
            'qty',
            'unit',
            'sr_no',
            'reading_from',
            'reading_to',
            'date',
            'doc__type',
            'doc__user_id',
            'user__user_name',
            'user__employee_id',
        )
    )
    

    a={'product_item_id': '1', 'product_item__product': 'GOPON -1000R -ONU (NORMAL ONU)', 'qty': '1', 'unit': 'PCS', 'sr_no': '1234567890', 'reading_from': '', 'reading_to': '', 'date': datetime.datetime(2025, 9, 26, 15, 1, 24, tzinfo=datetime.timezone.utc), 'doc__type': 'return', 'doc__user_id': 18, 'user__user_name': 'UMESH SONWANE', 'user__employee_id': 'ECS10002'}

    return render(req, "stocks_employee.html", {"stocks": stockdata, "employee": employee})



def find_employee(emp_id=None):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.get(API_BASE_URL, headers=headers)

    if response.status_code == 200:
        data = response.json()

        if isinstance(data, dict) and "response" in data:
            employees = data["response"]

            if emp_id:
                for emp in employees:
                    if emp.get("employee_id") == emp_id:
                        return emp   
                return None  

            return employees

        return []
    else:
        print(f"Error fetching employees: {response.status_code}")
        return None if emp_id else []


import pytz

# Define India timezone
india_tz = pytz.timezone("Asia/Kolkata")

# Get current time in India




def Issue(request, emp_id):
    try:
        employee = find_employee(emp_id)   # still external API
        products = StockItems.objects.all()
    except Exception as e:
        messages.error(request, f"Error: {e}")
        return redirect("issue", emp_id=emp_id)

    if request.method == "POST":
        products_list = request.POST.getlist("product[]")
        quantities = request.POST.getlist("quantity[]")
        units = request.POST.getlist("unit[]")
        serials = request.POST.getlist("serial_no[]", [])
        meters_from = request.POST.getlist("meter_from[]", [])
        meters_to = request.POST.getlist("meter_to[]", [])

        try:
            user_id = SuppUser.objects.only("user_id").get(employee_id=emp_id).user_id
            current_time = datetime.datetime.now(india_tz) 
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

            total_qty = sum(int(q) for q in quantities)

            with transaction.atomic():
                stock_ledger = StockLedger.objects.create(
                    type="ISSUE",
                    user_id=user_id,
                    qty=total_qty,
                    location="",
                    date=formatted_time,
                )

                line_items = []
                for i, product in enumerate(products_list):
                    unit = units[i]
                    sr_no, reading_from, reading_to = "", "", ""

                    if unit.lower() == "mtr":
                        reading_from = meters_from.pop(0) if meters_from else ""
                        reading_to = meters_to.pop(0) if meters_to else ""
                    else:
                        sr_no = serials.pop(0) if serials else ""

                    line_items.append(StockLedgerLineItems(
                        doc=stock_ledger,
                        user_id=user_id,
                        product_item_id=product,
                        qty=quantities[i],
                        unit=unit,
                        sr_no=sr_no,
                        reading_from=reading_from,
                        reading_to=reading_to,
                        date=formatted_time
                    ))

                StockLedgerLineItems.objects.bulk_create(line_items)

            messages.success(request, "✅ Stock issued successfully!")
        except Exception as e:
            print("Error:", e)
            messages.error(request, f"❌ Error while issuing product: {e}")

        return redirect("issue", emp_id=emp_id)

    return render(request, "issue.html", {"products": products, "employee": employee})



def return_products(request, emp_id):
    try:
        employee = find_employee(emp_id)
        products = StockItems.objects.all()
    except Exception as e:
        messages.error(request, f"Error: {e}")
        return redirect("return", emp_id=emp_id)

    if request.method == "POST":
        products_list = request.POST.getlist("product[]")
        quantities = request.POST.getlist("quantity[]")
        units = request.POST.getlist("unit[]")
        serials = request.POST.getlist("serial_no[]", [])
        meters_from = request.POST.getlist("meter_from[]", [])
        meters_to = request.POST.getlist("meter_to[]", [])

        try:
            user_id = SuppUser.objects.only("user_id").get(employee_id=emp_id).user_id
            current_time = datetime.datetime.now(india_tz) 
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

            total_qty = sum(int(q) for q in quantities)

            with transaction.atomic():
                stock_ledger = StockLedger.objects.create(
                    type="RETURN",
                    user_id=user_id,
                    qty=total_qty,
                    location="",
                    date=formatted_time,
                )

                line_items = []
                for i, product in enumerate(products_list):
                    unit = units[i]
                    sr_no, reading_from, reading_to = "", "", ""

                    if unit.lower() == "mtr":
                        reading_from = meters_from.pop(0) if meters_from else ""
                        reading_to = meters_to.pop(0) if meters_to else ""
                    else:
                        sr_no = serials.pop(0) if serials else ""

                    line_items.append(StockLedgerLineItems(
                        doc=stock_ledger,
                        user_id=user_id,
                        product_item_id=product,
                        qty=quantities[i],
                        unit=unit,
                        sr_no=sr_no,
                        reading_from=reading_from,
                        reading_to=reading_to,
                        date=formatted_time
                    ))

                StockLedgerLineItems.objects.bulk_create(line_items)

            messages.success(request, "✅ Stock returned successfully!")
        except Exception as e:
            print("Error:", e)
            messages.error(request, f"❌ Error while returning product: {e}")

        return redirect("return", emp_id=emp_id)

    return render(request, "return.html", {"products": products, "employee": employee})

def download_report(request):
    if request.method == "POST":
        from_date = request.POST.get("from_date")
        to_date = request.POST.get("to_date")
        report_type = request.POST.get("tabs1")   # issue / return / all
        file_type = request.POST.get("tabs2")     # xlsx / pdf / csv

        # Print the received values to the console (for debugging)
        print("Received Data =>")
        print("From Date:", from_date)
        print("To Date:", to_date)
        print("Report Type:", report_type)
        print("File Type:", file_type)

        # Return a simple JSON response so frontend doesn’t throw errors
        return JsonResponse({"message": "Data received successfully"})

    # Handle non-POST requests gracefully
    return JsonResponse({"error": "Invalid request method"}, status=405)

def network(request):
    return render(request, 'network.html')



def data(request):
    return render(request, 'data.html')



def inventory(request):
    return render(request, 'add_items.html')



def update_items(request):
    return render(request, 'update_items.html')


#playaround
def sample(req):
    return render(req, 'rough.html')