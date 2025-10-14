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
import io
import pandas as pd
from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.conf import settings
import os
from itsdangerous import URLSafeSerializer
import urllib.parse

API_BASE_URL = "http://api.elxer.com/v2/elxerone/agent-list"  
API_TOKEN = "36A9F18467C3EFD17E223FA46A3E4"  

SECRET_KEY = "super-secret-key"


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
        report_type = request.POST.get("tabs1")
        file_type = request.POST.get("tabs2")
        emp_id = request.POST.get("emp_id")
        #fetch data from DB based on from_date and to_date
        from_date_obj = datetime.datetime.strptime(from_date, "%Y-%m-%d")
        to_date_obj = datetime.datetime.strptime(to_date, "%Y-%m-%d")
        action = request.POST.get("action")
        print(f"Action: {action}")
        
        fetch_data=stockdata(emp_id,from_date_obj,to_date_obj,report_type)

        # Debug print
        print(f"Received Data => From: {from_date}, To: {to_date}, {report_type}")

        # Fetch data
        
        df = pd.DataFrame(list(fetch_data))

        # Make datetime columns timezone naive
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                if getattr(df[col].dt, 'tz', None) is not None:
                    df[col] = df[col].dt.tz_convert(None)
        df.rename(columns={
            'user__employee_id': 'Employee ID',
            'user__user_name': 'Employee Name',
            'date': 'Transaction Date',
            'doc__type': 'Document Type',
            'product_item__product': 'Product',
            'qty': 'Quantity',
            'unit': 'Unit',
            'sr_no': 'Serial No',
            'reading_from': 'Reading From',
            'reading_to': 'Reading To',
        }, inplace=True)
        
        
            
        output = io.BytesIO()
        if file_type.lower() == "xlsx":
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Products')
        
            output.seek(0)

            return FileResponse(
                output,
                as_attachment=True,
                filename="Stocks.xlsx",
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        elif file_type.lower() == "csv":
            df.to_csv(output, index=False, encoding='utf-8')
            output.seek(0)
            filename = f"Stocks_{report_type}_{from_date}_to_{to_date}.csv"
            content_type = 'text/csv'
            response = FileResponse(output, as_attachment=True, filename=filename, content_type=content_type)
            return response
        
        elif file_type.lower() == "pdf":
            return generate_pdf_report(request,df, from_date, to_date, report_type,action)
        else:
            return HttpResponse("Invalid file type", status=400)

    return HttpResponse("Invalid request method", status=400)


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

def stockdata(emp_id,from_date_obj,to_date_obj,type):
    if type == "issue" or type == "return":
        stockdata = (StockLedgerLineItems.objects
                .select_related('doc', 'user', 'product_item')
                .filter(
                    user__employee_id=emp_id,
                    date__date__range=(from_date_obj, to_date_obj),doc__type=type)
                .values(
                    'user__employee_id',
                    'user__user_name',
                    'date',
                    'doc__type',
                    'product_item__product',
                    'qty',
                    'unit',
                    'sr_no',
                    'reading_from',
                    'reading_to',
                )
            )
        return stockdata
    else:
        stockdata = (StockLedgerLineItems.objects
                .select_related('doc', 'user', 'product_item')
                .filter(
                    user__employee_id=emp_id,
                    date__date__range=(from_date_obj, to_date_obj)
                )
                .values(
                    'user__employee_id',
                    'user__user_name',
                    'date',
                    'doc__type',
                    'product_item__product',
                    'qty',
                    'unit',
                    'sr_no',
                    'reading_from',
                    'reading_to',
                )
            )
        return stockdata
    


def generate_pdf_report(request, df, from_date, to_date, report_type, action="download"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []
    
    filename = f"Stocks_{report_type}_{from_date}_to_{to_date}.pdf"
    output_filepath = os.path.join(settings.MEDIA_ROOT, filename)
        
        # Ensure the media directory exists before writing
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    styles = getSampleStyleSheet()
    elements.append(
    Paragraph('<font color="#0077db">Elxer Employee Stock Report</font>',styles["Title"]
    )
)
    elements.append(Paragraph(f"Report Type: {report_type}", styles["Normal"]))
    elements.append(Paragraph(f"From: {from_date}  To: {to_date}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Convert dataframe to list of lists
    data = [df.columns.tolist()] + df.values.tolist()

    # Create table with minimal styling
    table = Table(data, hAlign='CENTER')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0077db")),  # header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),                 # header text
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F3F3FF")])
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)  
     
    with open(output_filepath, "wb") as f:
        f.write(buffer.getvalue())
    print(f"Report successfully saved to {output_filepath}")
    base_url = "http://127.0.0.1:8000"
    file_url = base_url + settings.MEDIA_URL + filename
    short_url = shorten_link(file_url)
    print(f"Shortened URL: {short_url}")
    message = urllib.parse.quote(f"Hello, your requested stock report is ready.")
    if action == "share":
        return redirect(f"https://wa.me/?text={message}{short_url}")
    else:
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"Stocks_{report_type}_{from_date}_to_{to_date}.pdf",
            content_type='application/pdf'
        )
    
    
    
#link shortner for security
def shorten_link(file_relative_path):
    """
    Shortens a given URL into a secure encoded token-based short link.
    """
    serializer = URLSafeSerializer(secret_key=SECRET_KEY)
    token = serializer.dumps(file_relative_path)  
    
    return token



def share_report(req):
    if req.method == "POST":
        action = req.POST.get("action")
        print(f"Action: {action}")
        
        
    return redirect(req.META.get('HTTP_REFERER', '/'))  # Redirect back to the previous page