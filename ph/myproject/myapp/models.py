from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Default values for start and end time
def default_start_time():
    return "09:00:00"

def default_end_time():
    return "18:00:00"

class Pharmacy(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    P_id = models.IntegerField(primary_key=True)
    P_name = models.CharField(max_length=100)
    contact_info = models.CharField(max_length=13)
    location = models.CharField(max_length=100, default='Unknown Location')
    start_time = models.TimeField(default=default_start_time)
    end_time = models.TimeField(default=default_end_time)
    status = models.CharField(max_length=20, default='pending')
    stock_level = models.CharField(max_length=100, default='high')
    password = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.P_name


    def save(self, *args, **kwargs):
        # Assign the next available ID if none is provided
        if not self.P_id:
            max_id = Pharmacy.objects.aggregate(models.Max('P_id'))['P_id__max']
            self.P_id = (max_id or 0) + 1
        super().save(*args, **kwargs)

    @staticmethod
    def reorder_ids():
        """
        Reorders all IDs sequentially, starting from 1.
        """
        pharmacies = Pharmacy.objects.order_by('P_id')  # Fetch records sorted by current ID
        for index, pharmacy in enumerate(pharmacies, start=1):
            pharmacy.P_id = index  # Reassign ID sequentially
            pharmacy.save()  # Save the updated ID to the database

    def delete(self, *args, **kwargs):
        """
        Override the delete method to reorder IDs after deletion.
        """
        super().delete(*args, **kwargs)
        Pharmacy.reorder_ids()  # Reorder IDs after a record is deleted

    def __str__(self):
        return self.P_name

    
class Supplier(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    S_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)  # Changed to CharField for flexibility

    def __str__(self):
        return self.name
    

class Notification(models.Model):
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, null=False)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)  # Track if notification is read
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Notification: {self.message}"
    

class Medicine(models.Model):
    M_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True, null=False)  # Add serial_number
    exp_date = models.DateField(null=False)  # Add expiration date field
    MFG_date = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False, default=0.0)

    def __str__(self):
        return self.name
    

from django.db import models
from django.utils import timezone

class Order(models.Model):
    O_id = models.AutoField(primary_key=True)  # Auto-incrementing order ID
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='orders')  # The pharmacy placing the order
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='orders')  # The supplier receiving the order
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField()  # Quantity of medicine being ordered
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # Total price of the order
    order_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ], default='pending')  # Order status
    order_date = models.DateTimeField(default=timezone.now)  # Date and time of the order
    delivery_date = models.DateTimeField(blank=True, null=True)  # Expected delivery date (optional)

    def calculate_total_price(self):
        """
        Automatically calculate the total price based on medicine price and quantity.
        """
        self.total_price = self.medicine.price * self.quantity

    def save(self, *args, **kwargs):
        """
        Override save to ensure total price is calculated before saving.
        """
        self.calculate_total_price()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.O_id} by {self.pharmacy} to {self.supplier}"    

class Message(models.Model):
    NOTIFICATION_TYPES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    receiver_pharmacy = models.CharField(max_length=255)
    sender = models.CharField(max_length=255, default='Unknown Sender')  # Added sender field
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # Add this field

    def __str__(self):
        return self.title
    

class Pmedstock(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    weight = models.CharField(max_length=100)
    category = models.CharField(max_length=100)  # You can also use a ForeignKey if you have a Category model
    manufacturer = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    manufacturer_price = models.DecimalField(max_digits=10, decimal_places=2)
    expire_date = models.DateField()
    stock = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    details = models.TextField()

    def __str__(self):
        return self.name
    




