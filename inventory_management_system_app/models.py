from django.db import models

class SuppUser(models.Model):
    user_id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=50)
    user_email = models.CharField(unique=True, max_length=50)
    user_pass = models.CharField(max_length=250)
    page_role = models.CharField(max_length=13, blank=True, null=True)
    employee_id = models.CharField(max_length=255)
    user_mobile = models.CharField(max_length=12)
    time_stamp = models.CharField(max_length=25)
    franchise_id = models.CharField(max_length=25)
    group_id = models.TextField()
    enabled = models.CharField(max_length=3, blank=True, null=True)
    department = models.TextField()
    phone_ip = models.CharField(max_length=25, blank=True, null=True)
    extension = models.CharField(max_length=255, blank=True, null=True)
    onesignal_player_id = models.CharField(max_length=255, blank=True, null=True)
    telegram_chat_id = models.CharField(max_length=255, blank=True, null=True)
    is_logged_in = models.CharField(max_length=1)
    last_accessed_at = models.DateTimeField()
    is_queue_panel = models.IntegerField(db_comment='1 - access, 0 - not access')

    class Meta:
        managed = False
        db_table = 'supp_user'


class StockItems(models.Model):
    id = models.BigAutoField(primary_key=True)
    product = models.CharField(max_length=255)
    unit = models.CharField(max_length=3)
    qty = models.IntegerField()
    alert_qty = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'stock_items'


class StockLedger(models.Model):
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=6)
    user = models.ForeignKey(SuppUser, on_delete=models.CASCADE)  # ForeignKey to SuppUser
    qty = models.CharField(max_length=255)
    location = models.TextField()
    date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'stock_ledger'


class StockLedgerLineItems(models.Model):
    id = models.BigAutoField(primary_key=True)
    doc = models.ForeignKey(StockLedger, on_delete=models.CASCADE, db_column='doc_id') 
    user = models.ForeignKey(SuppUser, on_delete=models.CASCADE, db_column='user_id')
    product_item = models.ForeignKey(StockItems, on_delete=models.CASCADE, db_column='product')
    qty = models.CharField(max_length=255)
    unit = models.CharField(max_length=3)
    sr_no = models.CharField(max_length=255)
    reading_from = models.CharField(max_length=255)
    reading_to = models.CharField(max_length=255)
    date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'stock_ledger_line_items'

