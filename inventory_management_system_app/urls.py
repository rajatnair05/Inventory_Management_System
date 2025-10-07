# # from inventory_management_system_app import views
# from django.urls import path, include
# from .views import *
# # from .views import login

# urlpatterns=[
#     # path('', login, name='login'),
#     path('signup', signup, name='signup'),
#     path('stocks/',stocks, name='stocks'),
#     path('inventory/',inventory, name='inventory'),
#     path('data/', data, name='data'),
#     path('network/', network, name='network'),
#     path('', dashboard, name='dashboard'),
#     path('add_items/', add_items, name='items'),
#     path('update_items/', update_items, name='update_items'),
#     path('employee_Stock_Detail/',Employee_stock_detail, name="Employee_stock_Detail"),
#     path('issue/<str:emp_id>', Issue, name='issue'),
#     path('return/<str:emp_id>', return_products, name='return'),
# ]

# from inventory_management_system_app import views
from django.urls import path, include
from .views import *
# from .views import login

urlpatterns=[
    path('sample', sample, name=''),
    path('signup', signup, name='signup'),
    path('stocks/',stocks, name='stocks'),
    path('inventory/',inventory, name='inventory'),
    path('data/', data, name='data'),
    path('network/', network, name='network'),
    path('', dashboard, name='dashboard'),
    # path('add_items/', add_items, name='items'),
    path('update_items/', update_items, name='update_items'),
    path('employee_Stock_Detail/<str:emp_id>/',Employee_stock_detail, name="Employee_stock_Detail"),
    path('issue/<str:emp_id>/', Issue, name='issue'),
    path('return/<str:emp_id>/', return_products, name='return'),
    path("download-report/", download_report, name="download_report"),
]