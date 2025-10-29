from django.shortcuts import render, redirect, get_object_or_404
import json
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
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
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from django.http import FileResponse, HttpResponse, Http404
from .extra_addins import get_zen_quote
import re
from datetime import timedelta
import os
import sys
import django
from django.urls import reverse

india_tz = pytz.timezone("Asia/Kolkata")


API_BASE_URL = "http://api.elxer.com/v2/elxerone/agent-list"  
API_TOKEN = "36A9F18467C3EFD17E223FA46A3E4"  

SECRET_KEY = "super-secret-key"
curr_date_time_find = datetime.datetime.now(india_tz).strftime("%Y-%m-%d %H:%M:%S")
curr_date_time=curr_date_time_find.replace(" ","_").replace(":","-")

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
    file_validity_checker()
    quotes = get_zen_quote()
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
    
    return render(req, "stocks_employee.html", {"stocks": stockdata, "employee": employee,'quotes':quotes})



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



def shorten_link(filename):
    """
    Generates a secure, time-limited token for file download.
    """
    serializer = URLSafeTimedSerializer(secret_key=SECRET_KEY)
    token = serializer.dumps(filename)
    return token

def download_file(request, token):
    """
    Serves the file for download via a secure token.
    """
    serializer = URLSafeTimedSerializer(secret_key=SECRET_KEY)
    try:
        # Token valid for 1 hour
        print("download link accessed")
        filename = serializer.loads(token, max_age=3600)
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        if os.path.exists(file_path):
            return FileResponse(open(file_path, 'rb'), as_attachment=True)
            
        else:
            raise Http404("File not found.")
    except SignatureExpired:
        
        raise Http404("Link expired.")
    except BadSignature:
        raise Http404("Invalid link.")

# ===============================
# 🔹 STOCK DATA FETCH LOGIC
# ===============================
def stockdata(emp_id, from_date_obj, to_date_obj, type):
    if type == "issue" or type == "return":
        stockdata = (
            StockLedgerLineItems.objects
            .select_related('doc', 'user', 'product_item')
            .filter(
                user__employee_id=emp_id,
                date__date__range=(from_date_obj, to_date_obj),
                doc__type=type
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
    else:
        stockdata = (
            StockLedgerLineItems.objects
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

# ===============================
# 🔹 DOWNLOAD REPORT
# ===============================
def download_report(request):
    if request.method == "POST":
        from_date = request.POST.get("from_date")
        to_date = request.POST.get("to_date")
        report_type = request.POST.get("tabs1")
        file_type = request.POST.get("tabs2")
        emp_id = request.POST.get("emp_id")
        action = request.POST.get("action")  # "download" or "share"

        # Debug print
        print(f"Action: {action}")
        print(f"Received Data => From: {from_date}, To: {to_date}, {report_type}")

        # Convert to datetime
        from_date_obj = datetime.datetime.strptime(from_date, "%Y-%m-%d")
        to_date_obj = datetime.datetime.strptime(to_date, "%Y-%m-%d")

        # Fetch data
        fetch_data = stockdata(emp_id, from_date_obj, to_date_obj, report_type)
        df = pd.DataFrame(list(fetch_data))

        # Make datetime columns timezone naive
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                if getattr(df[col].dt, 'tz', None) is not None:
                    df[col] = df[col].dt.tz_convert(None)

        # Rename columns
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

        # ===============================
        # Generate files based on type
        # ===============================
        
        output = io.BytesIO()
        if file_type.lower() == "xlsx":
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Products')
            output.seek(0)
            
            #share a link when action is share
            if action == "share":
                filename = f"Stocks_{report_type}_{from_date}_to_{to_date}_{(curr_date_time)}.xlsx"
                with open(os.path.join(settings.MEDIA_ROOT, filename), "wb") as f:  
                    f.write(output.getvalue())
                    
                shareablelink,message_text = file_Serve_for_share(filename)
                
                return JsonResponse({
            "share_url": shareablelink,
            "message_text": message_text
        })
            else:
                return FileResponse(
                    output,
                    as_attachment=True,
                    filename=f"Stocks_{report_type}_{from_date}_to_{to_date}_{(curr_date_time)}.xlsx",
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
        elif file_type.lower() == "csv":
            df.to_csv(output, index=False, encoding='utf-8')
            output.seek(0)
            filename = f"Stocks_{report_type}_{from_date}_to_{to_date}_{(curr_date_time)}.csv"
            #share a link when action is share
            if action == "share":
                filename = f"Stocks_{report_type}_{from_date}_to_{to_date}_{(curr_date_time)}.csv"
                with open(os.path.join(settings.MEDIA_ROOT, filename), "wb") as f:  
                    f.write(output.getvalue())
                
                shareablelink,message_text = file_Serve_for_share(filename)
                
                return JsonResponse({
            "share_url": shareablelink,
            "message_text": message_text
        })
            else:    
                return FileResponse(output, as_attachment=True, filename=filename, content_type='text/csv')
        elif file_type.lower() == "pdf":
            return generate_pdf_report(request, df, from_date, to_date, report_type, action)
        else:
            return HttpResponse("Invalid file type", status=400)

    return HttpResponse("Invalid request method", status=400)

# ===============================
# 🔹 PDF REPORT GENERATOR
# ===============================
def generate_pdf_report(request, df, from_date, to_date, report_type, action="download"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []

    filename = f"Stocks_{report_type}_{from_date}_to_{to_date}_{curr_date_time}.pdf"
    output_filepath = os.path.join(settings.MEDIA_ROOT, filename)
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    styles = getSampleStyleSheet()
    elements.append(Paragraph('<font color="#0077db">Elxer Employee Stock Report</font>', styles["Title"]))
    elements.append(Paragraph(f"Report Type: {report_type}", styles["Normal"]))
    elements.append(Paragraph(f"From: {from_date}  To: {to_date}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Convert dataframe to list of lists
    data = [df.columns.tolist()] + df.values.tolist()
    table = Table(data, hAlign='CENTER')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0077db")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
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

    # Save PDF locally
    
    if action == "share":
        with open(output_filepath, "wb") as f:
            f.write(buffer.getvalue())
            print(f"Report saved to {output_filepath}")

        shareablelink,message_text = file_Serve_for_share(filename)
                
        return JsonResponse({
            "share_url": shareablelink,
            "message_text": message_text
        })
    else:
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type='application/pdf'
        )



import requests

def shorten_link_tinyurl(long_url):
    """
    Shortens a given URL using TinyURL API.

    Args:
        long_url (str): The original URL to shorten.

    Returns:
        str: Shortened TinyURL if successful, else the original URL.
    """
    api_url = f"http://tinyurl.com/api-create.php?url={long_url}"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        short_url = response.text
        return short_url
    except requests.exceptions.RequestException as e:
        print(f"Error shortening URL via TinyURL: {e}")
        return long_url

# ===============================
# 🔹 SAMPLE PAGES
# ===============================
def network(request):
    return render(request, 'network.html')

def data(request):
    return render(request, 'data.html')

def inventory(request):
    return render(request, 'add_items.html')

def update_items(request):
    return render(request, 'update_items.html')

def sample(req):
    return render(req, 'sample.html')



def file_Serve_for_share(filename):
    token = shorten_link(filename)
    download_link = f"http://127.0.0.1:8000/download/{token}/"
    print(f"Download link: {download_link}")
    shareable_link = shorten_link_tinyurl(download_link)
    print(f"Shortened link: {shareable_link}")
    # WhatsApp message
    message = f"Hello! Your requested stock report is ready.%0A%0ADownload here: {shareable_link}"
    return shareable_link,message


def file_validity_checker():

    project_root = r"C:\Users\rajat.n_elxer\OneDrive\Desktop\Ims\Inventory_Management_System"
    sys.path.append(project_root)

    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "inventory_management_system_project.settings"
    )

    django.setup()

    # ---------------------------
    # 4. Import settings
    from django.conf import settings

    # MEDIA folder path
    folder_path = settings.MEDIA_ROOT
    print("Media folder path:", folder_path)

    # ---------------------------
    # 5. Regex pattern to match date and time in filenames
    # Example filename: report_2025-10-18_14-30-00.pdf
    pattern = r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})"

    # Current datetime
    curr_datetime = datetime.datetime.now(india_tz).replace(microsecond=0)
    print("Current time in ims:", curr_datetime)

    # ---------------------------
    # 6. Loop through files in media folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if os.path.isfile(file_path):
            print("\nFilename:", filename)
            match = re.search(pattern, filename)
            if match:
                basedate, basetime = match.groups()
                basetime_colon = basetime.replace("-", ":")
                datetime_str = f"{basedate} {basetime_colon}"
                try:
                    dt_object1 = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                    dt_object = india_tz.localize(dt_object1)
                    difftime = curr_datetime - dt_object

                    
                    if difftime >= timedelta(hours=1):
                        print(f"Deleting file: {filename} | Time difference: {difftime}")
                        os.remove(file_path)
                    else:
                        print(f"File is recent: {filename} | Time difference: {difftime}")

                except ValueError:
                    print("Error: Could not parse datetime from filename")
            else:
                print("No datetime found in filename")