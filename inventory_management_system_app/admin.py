from django.contrib import admin
from .models import *

admin.site.register(StockItems)
admin.site.register(StockLedgerLineItems)
admin.site.register(StockLedger)
admin.site.register(SuppUser)