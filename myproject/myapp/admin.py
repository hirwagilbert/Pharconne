from django.contrib import admin
from .models import Pharmacy, Supplier, Notification, Medicine, Order, Message, Pmedstock

@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ('P_id', 'P_name', 'contact_info', 'location', 'start_time', 'end_time', 'status', 'stock_level', 'password')
    actions = ['update_stock_levels']

# Supplier Admin
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('S_id', 'name', 'contact', 'password')

# Notification Admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('pharmacy', 'message', 'created_at', 'is_read')

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('M_id', 'supplier', 'name', 'serial_number', 'exp_date', 'MFG_date', 'quantity', 'price', 'status')  # Customize which fields are displayed
    search_fields = ('name', 'serial_number')  # Allow search by name and serial_number
    list_filter = ('exp_date', 'MFG_date', 'price')

# Customize the admin display for Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('O_id', 'pharmacy', 'supplier', 'medicine', 'quantity', 'total_price', 'order_status', 'order_date', 'delivery_date')
    list_filter = ('order_status', 'order_date', 'delivery_date')  # Filter options in the sidebar
    search_fields = ('O_id', 'pharmacy__P_name', 'supplier__name', 'medicine__name')  # Search functionality
    ordering = ('-order_date',)  # Order by latest orders first


class MessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'message', 'receiver_pharmacy', 'sender', 'date', 'is_read', 'created_at')  # Fields to display in the admin list

admin.site.register(Message, MessageAdmin)  # Register the model with the admin site

@admin.register(Pmedstock)
class Pmedstock(admin.ModelAdmin):
    list_display = ('pharmacy', 'name', 'generic_name', 'sku', 'price', 'stock', 'status', 'expire_date')
    search_fields = ('name', 'generic_name', 'sku')
    list_filter = ('status', 'category')
    ordering = ('name',)





    





