from django.http import HttpResponse
from .forms import PharmacySignupForm
from .models import Pharmacy, Medicine, Supplier, Message, Pmedstock
from datetime import datetime
from .models import Notification, Order
from django.contrib import messages
from django.http import JsonResponse
from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import JsonResponse
import json
from .forms import MedicineForm
from datetime import timedelta
from django.db.models import Sum, Q, F
from django.db.models import Subquery
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
 


def login_view(request):
    if request.method == "POST":
        name = request.POST.get('name')  # Get 'name' from form
        password = request.POST.get('password')  # Get 'password' from form

        # 1. Check if the login is for an admin user (Django's User table)
        admin_user = authenticate(request, username=name, password=password)
        if admin_user is not None:
            login(request, admin_user)  # Log in the admin user
            request.session['user_name'] = admin_user.username  # Save admin's username
            request.session['user_type'] = 'admin'  # Set user type as admin
            return redirect('supplierd')  # Redirect to admin dashboard

        # 2. Check if the login is for a pharmacy user (custom Pharmacy table)
        try:
            pharmacy_user = Pharmacy.objects.get(Q(P_name=name) & Q(password=password))
            request.session['pharmacy_id'] = pharmacy_user.P_id
            request.session['user_name'] = pharmacy_user.P_name
            request.session['user_type'] = 'pharmacy'
            return redirect('userhome')  # Redirect to pharmacy dashboard

        except Pharmacy.DoesNotExist:
            pass  # Continue to check for Supplier login

        # 3. Check if the login is for a supplier user (Supplier table)
        try:
            supplier_user = Supplier.objects.get(Q(name=name) & Q(password=password))
            request.session['supplier_id'] = supplier_user.S_id
            request.session['user_name'] = supplier_user.name
            request.session['user_type'] = 'supplier'
            return redirect('supplierdashboard')  # Redirect to supplier dashboard

        except Supplier.DoesNotExist:
            pass  # If no matching supplier is found

        # 4. If no user is found
        messages.error(request, "Username or password is incorrect!")
        return redirect('login_view')  # Redirect back to the login page

    # Render the login form if GET request
    return render(request, 'myapp/login_view.html')


@login_required
def pharmacy_list(request):
    # Check if the logged-in user is part of the 'supplier' group
    is_supplier = request.user.groups.filter(name='supplier').exists()

    # Get the search query if provided
    search_query = request.GET.get('search', '')
    pharmacies = Pharmacy.objects.all()

    if search_query:
        pharmacies = pharmacies.filter(
            Q(P_name__icontains=search_query) |  # Search by pharmacy name
            Q(contact_info__icontains=search_query) |  # Search by contact info
            Q(location__icontains=search_query)  # Search by location
        )

    # Count unread notifications
    unread_notifications = Notification.objects.filter(is_read=False).count()

    # Pass the `is_supplier` variable to the template to control rendering based on user group
    return render(request, 'myapp/pharmacy_list.html', {
        'data': pharmacies,
        'search_query': search_query,  # Pass the search query to the template
        'unread_notifications': unread_notifications,
        'is_supplier': is_supplier,  # This will be used to conditionally display content in the template
    })


def pharmacy_list(request):
    search_query = request.GET.get('search', '')
    print(f"Search Query: {search_query}")  # Debug output

    # Use the correct field name (P_name) for filtering
    results = Pharmacy.objects.filter(P_name__icontains=search_query) if search_query else Pharmacy.objects.all()

    print(f"Results: {results}")  # Debug output
    
    context = {
        'search_query': search_query,
        'results': results,
    }
    
    return render(request, 'myapp/pharmacy_list.html', context)


@login_required
def logout_view(request):
    logout(request)  # Logs out the admin user
    request.session.flush()  # Clears all session data
    return redirect('login_view')  # Redirect to the login page


def add_member(request):
    if request.method == 'POST':
        pharmacy_name = request.POST.get('P_name')
        contact = request.POST.get('contact_info')
        location = request.POST.get('location', 'Unknown Location')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        password = request.POST.get('password')  # Handle password

        try:
            # Convert start_time and end_time strings to time objects
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()

            # Create a User instance for authentication (username = pharmacy_name, password = password)
            user = User.objects.create_user(username=pharmacy_name, password=password)

            # Save other data into the Pharmacy model
            pharmacy = Pharmacy.objects.create(
                P_name=pharmacy_name,
                contact_info=contact,
                location=location,
                start_time=start_time,
                end_time=end_time,
                status="pending",  # Default status is "pending"
                stock_level="high",  # Default stock level
                password=password,  # Optional: storing password here too
            )

            # Link the user with the pharmacy (optional, if you want a reference to the User)
            pharmacy.user = user
            pharmacy.save()

            # Create a notification for the new pharmacy registration
            Notification.objects.create(
                message=f"New pharmacy registration awaiting approval: {pharmacy_name}",
                pharmacy=pharmacy  # Link the pharmacy instance
            )
            
            # Success message
            messages.success(request, "Pharmacy registration pending approval.")
            return redirect('add_member')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return render(request, 'myapp/add_member.html')


def dashboard(request):
    # Get count of unread notifications
    unread_notifications = Notification.objects.filter(is_read=False)
    notification_count = unread_notifications.count()

    return render(request, 'myapp/pharmacy_list.html', {
        'notification_count': notification_count,
    })

#Mark Notifications as Read 
def mark_notification_as_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id)
    notification.is_read = True
    notification.save()
    return redirect('dashboard')

def notification(request):
    notifications = Notification.objects.all().order_by('-created_at')

    # Mark notifications as read
    Notification.objects.filter(is_read=False).update(is_read=True)

    return render(request, 'myapp/notification.html', {
        'notifications': notifications,
    })

def get_unread_count(request):
    unread_count = Notification.objects.filter(is_read=False).count()
    return JsonResponse({'unread_count': unread_count})

#Add views to handle approve and delete operations for notifications.
def approve_notification(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id, is_read=False)

        # Mark the notification as read
        notification.is_read = True
        notification.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)


def delete_notification(request, notification_id):
    if request.method == 'POST':
        # Get the notification
        notification = get_object_or_404(Notification, id=notification_id)

        # Check if the notification has an associated pharmacy and delete it
        if notification.pharmacy:
            notification.pharmacy.delete()

        # Delete the notification itself
        notification.delete()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)

def pharmacy_detail(request, pharmacy_id):
    pharmacy = get_object_or_404(Pharmacy)
    notification = Notification.objects.filter(pharmacy=pharmacy).last()  # Or any other logic for fetching the notification
    return render(request, 'myapp/pharmacy_detail.html', {'pharmacy': pharmacy, 'notification': notification})


def notification_list(request):
    data = Notification.objects.all()  # or filter based on your needs
    return render(request, 'your_template.html', {'data': data})


def pharmacy_list(request):
    data = Pharmacy.objects.all()
    return render(request, 'myapp/pharmacy_list.html', {'data': data})


@login_required
def edit_pharmacy_profile(request):
    # Retrieve the logged-in pharmacy ID from the session
    pharmacy_id = request.session.get('pharmacy_id')
    if not pharmacy_id:
        messages.error(request, "No pharmacy user logged in.")
        return redirect('login_view')

    try:
        # Fetch the logged-in pharmacy user
        pharmacy = Pharmacy.objects.get(P_id=pharmacy_id)

        if request.method == "POST":
            # Update pharmacy details with form data
            pharmacy.P_name = request.POST.get('P_name', pharmacy.P_name)
            pharmacy.contact_info = request.POST.get('contact_info', pharmacy.contact_info)
            pharmacy.location = request.POST.get('location', pharmacy.location)
            pharmacy.password = request.POST.get('password', pharmacy.password)
            pharmacy.save()

            messages.success(request, "Profile updated successfully.")
            return redirect('pharmacy_list')  # Redirect after updating profile

        # Pass the pharmacy object to the template
        return render(request, 'myapp/pharmacy_profile.html', {'pharmacy': pharmacy})

    except Pharmacy.DoesNotExist:
        messages.error(request, "Pharmacy user not found.")
        return redirect('login_view')


def order_medicine(request):
    if request.method == 'POST':
        pharmacy_name = request.POST.get('pharmacy_name').strip()
        medicine_name = request.POST.get('medicine_name').strip()
        quantity = request.POST.get('quantity')
        supplier_id = request.POST.get('supplier_id')
        price = request.POST.get('price')  # Capture the price from the form
        order_date = timezone.now()

        # Validate quantity
        if not quantity.isdigit() or int(quantity) <= 0:
            messages.error(request, "Quantity must be a valid positive number.")
            return render(request, 'myapp/ordering.html', {
                'suppliers': Supplier.objects.all(),
                'medicines': Medicine.objects.all()  # Pass medicines to the template
            })

        # Validate price
        if price is None or price.strip() == "":
            messages.error(request, "Price is required.")
            return render(request, 'myapp/ordering.html', {
                'suppliers': Supplier.objects.all(),
                'medicines': Medicine.objects.all()
            })

        try:
            price = float(price)  # Convert to float
            if price < 0:
                raise ValueError("Price must be a positive number.")
        except ValueError:
            messages.error(request, "Price must be a valid positive number.")
            return render(request, 'myapp/ordering.html', {
                'suppliers': Supplier.objects.all(),
                'medicines': Medicine.objects.all()
            })

        quantity = int(quantity)

        # Fetching the related pharmacy and supplier
        try:
            pharmacy = Pharmacy.objects.get(P_name=pharmacy_name)
            supplier = Supplier.objects.get(S_id=supplier_id)
        except (Pharmacy.DoesNotExist, Supplier.DoesNotExist) as e:
            messages.error(request, f"Error: {str(e)}")
            return render(request, 'myapp/ordering.html', {
                'suppliers': Supplier.objects.all(),
                'medicines': Medicine.objects.all(),
            })

        # Create or get the medicine from the Medicinee table
        medicine, created = Medicine.objects.get_or_create(
            name=medicine_name,
            defaults={'exp_date': timezone.now(), 'price': price}  # Provide price here
        )

        # Create and save the order
        try:
            order = Order.objects.create(
                pharmacy=pharmacy,
                supplier=supplier,
                medicine=medicine,  # This should now correctly reference Medicinee
                quantity=quantity,
                order_date=order_date
            )
            order.save()
            messages.success(request, "Ordering pending approval.")
            return redirect('userdash')
        except IntegrityError:
            messages.error(request, "Failed to create order due to integrity constraints.")
        except Exception as e:
            messages.error(request, f"Failed to create order: {str(e)}")

    # Fetch all medicines to display in the dropdown
    medicines = Medicine.objects.all()

    return render(request, 'myapp/ordering.html', {
        'suppliers': Supplier.objects.all(),
        'medicines': medicines,  # Pass medicines to the template
    })


def search_medicine(request):
    query = request.GET.get('q', '')
    if query:
        medicines = Medicine.objects.filter(name__icontains=query)[:10]  # Limit to 10 suggestions
        suggestions = [{'name': medicine.name} for medicine in medicines]
    else:
        suggestions = []

    return JsonResponse({'suggestions': suggestions})


def current_orders(request):
    logged_in_pharmacy_name = request.session.get('user_name')

    orders = Order.objects.filter(pharmacy__P_name=logged_in_pharmacy_name)

    return render(request, 'myapp/pharorder.html', {'orders': orders})


def message_list(request):
    logged_in_pharmacy_name = request.session.get('user_name')

    messages = Message.objects.filter(receiver_pharmacy=logged_in_pharmacy_name)

    # Check if messages exist
    if messages.exists():
        message_data = messages
    else:
        message_data = None 

    return render(request, "myapp/message_list.html", {
        'messages': message_data,
        'no_messages_found': not messages.exists(), 
    })


def view_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    message.is_read = True  # Mark the message as read
    message.save()  # Save the changes
    return render(request, 'myapp/message_list.html', {'message': message})

def mark_as_read(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if not message.is_read:
        message.is_read = True
        message.save()
    return JsonResponse({'status': 'success'})

def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    
    if request.method == 'POST':
        message.delete()
        return redirect('message_list')  # Redirect after deletion

    return render(request, 'myapp/message_list.html', {'message': message})


def create_notification(request):
    # Fetch all pharmacies from the database
    pharmacies = Pharmacy.objects.all()

    if request.method == 'POST':
        # Get data from the request
        title = request.POST.get('title')
        message = request.POST.get('message')
        message_type = request.POST.get('message_type')
        receiver_pharmacy = request.POST.get('receiver_pharmacy')
        sender = request.POST.get('sender_name')
        date = request.POST.get('notification_date')

        # Create and save the message
        new_message = Message(
            title=title,
            message=message,
            type=message_type,
            receiver_pharmacy=receiver_pharmacy,
            sender=sender,
            date=date,
        )
        new_message.save()

        # Redirect to the message list page
        return redirect('notification')

    # Render the form with the list of pharmacies
    return render(request, 'myapp/send.html', {'pharmacies': pharmacies})


def reply_message(request, message_id):
    original_message = get_object_or_404(Message, id=message_id)

    if request.method == 'POST':
        # Get data from the form
        reply_message_text = request.POST.get('message')
        sender_name = request.POST.get('sender_name')

        # Create and save the notification (reply)
        # Get the pharmacy instance
        receiver_pharmacy = get_object_or_404(Pharmacy, P_id=original_message.receiver_pharmacy)

        new_notification = Notification(
            pharmacy=receiver_pharmacy,  # Set the pharmacy from the original message
            message=reply_message_text,
            created_at=timezone.now(),  # Set to current time
        )
        new_notification.save()

        return redirect('message_list')  # Redirect to the message list after replying

    return render(request, 'myapp/reply_message.html', {'original_message': original_message})

def dashboard(request):
    total_medicines = Medicine.objects.count()
    total_pharmacies = Pharmacy.objects.count()
    total_suppliers = Supplier.objects.count()
    
    # Fetch all pharmacies
    pharmacies = Pharmacy.objects.all()  # Get all pharmacy instances
    
    context = {
        'total_medicines': total_medicines,
        'total_pharmacies': total_pharmacies,
        'total_suppliers': total_suppliers,
        'pharmacies': pharmacies,  # Add pharmacies to context
    }
    
    return render(request, 'myapp/dashboard.html', context)


def pharmaddmedicine(request):
    if request.method == "POST":
        pharmacy = request.POST['pharmacy_name']
        name = request.POST['medicineName']
        generic_name = request.POST['genericName']
        sku = request.POST['sku']
        weight = request.POST['weight']
        category = request.POST['category']
        manufacture = request.POST['manufacture']
        price = request.POST['price']
        manufacturer_price = request.POST['manufacturerPrice']
        expire_date = request.POST['expireDate']
        stock = request.POST['stock']
        status = request.POST['status']
        details = request.POST['details']

        # Create a new Pmedstock entry
        Pmedstock.objects.create(
            pharmacy = pharmacy,
            name=name,
            generic_name=generic_name,
            sku=sku,
            weight=weight,
            category=category,
            manufacture=manufacture,
            price=price,
            manufacturer_price=manufacturer_price,
            expire_date=expire_date,
            stock=stock,
            status=status,
            details=details,
        )

        return redirect('userhome')  # Redirect to a success page or the same page

    return render(request, 'myapp/pharmaddmedicine.html')  # Render the form if not POST


def medview(request):
    data = Pmedstock.objects.all()
    return render(request, 'myapp/medicineview.html', {
        'data': data
    })

def meddetails(request):
    data = Pmedstock.objects.all()
    return render(request, 'myapp/medicinedetails.html', {
        'data': data
    })


@login_required
@csrf_exempt  # Use only if you're not using CSRF tokens in your AJAX requests
def reset_password(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_password = data.get('new_password')

        if new_password:
            # Check if the user is associated with a Pharmacy
            try:
                pharmacy = Pharmacy.objects.get(user=request.user)  # Assuming there is a ForeignKey from Pharmacy to User
                pharmacy.set_password(new_password)  # Update password
                pharmacy.save()  # Save the pharmacy instance
                return JsonResponse({'success': True})

            except Pharmacy.DoesNotExist:
                # Check if the user is associated with a Supplier
                try:
                    supplier = Supplier.objects.get(user=request.user)  # Assuming there is a ForeignKey from Supplier to User
                    supplier.set_password(new_password)  # Update password
                    supplier.save()  # Save the supplier instance
                    return JsonResponse({'success': True})

                except Supplier.DoesNotExist:
                    return JsonResponse({'error': 'User type not recognized'}, status=400)

        return JsonResponse({'error': 'Invalid password'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def add_medicine(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('medicine_success')  # Redirect to a success page
    else:
        form = MedicineForm()
    return render(request, 'myapp/add_medicine.html', {'form': form})

# Success view
def medicine_success(request):
    # Query all medicines from the Medicine table
    medicines = Medicine.objects.all()
    
    # Pass the medicines data to the template
    return render(request, 'myapp/medicine_success.html', {'medicines': medicines})


def edit_medicine(request, M_id):
    medicine = get_object_or_404(Medicine, M_id=M_id)  
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            return redirect('medicine_success')
    else:
        form = MedicineForm(instance=medicine)
    return render(request, 'myapp/edit_medicine.html', {'form': form})


def delete_medicine(request, M_id):
    medicine = get_object_or_404(Medicine, M_id=M_id)  
    if request.method == 'POST':
        medicine.delete()
        return redirect('medicine_success')
    return render(request, 'myapp/delete_medecine.html', {'medicine': medicine})


def medicine_success(request):
    medicines = Medicine.objects.all()  # Ensure this is the correct model
    return render(request, 'myapp/medicine_success.html', {'medicines': medicines})


def supplierd(request):
    total_medicines = Medicine.objects.count()  # Get the total count of medicines
    total_pharmacies = Pharmacy.objects.count()  # Get the total count of pharmacies
    total_suppliers = Supplier.objects.count()  # Get the total count of suppliers

    # Current date
    current_date = timezone.now().date()

    # Calculate the date 60 days from now
    notification_date = current_date + timedelta(days=60)

    # Initialize notification lists
    notifications = []

    # Check and delete expired medicines in Pmedstock
    pmedstock_expired = Pmedstock.objects.filter(expire_date__lte=current_date)
    for item in pmedstock_expired:
        notifications.append({
            'type': 'expired',
            'color': 'orange',
            'message': f"Medicine '{item.name}' has expired on {item.expire_date} and will be removed."
        })
    pmedstock_expired.delete()  # Remove expired medicines from Pmedstock

    # Check Pmedstock for nearing expiration dates
    pmedstock_warnings = Pmedstock.objects.filter(expire_date__gt=current_date, expire_date__lte=notification_date)
    for item in pmedstock_warnings:
        notifications.append({
            'type': 'expire',
            'color': 'yellow',
            'message': f"Medicine '{item.name}' will expire on {item.expire_date}."
        })

    # Check and delete expired medicines in Medicine
    medicine_expired = Medicine.objects.filter(exp_date__lte=current_date)
    for medicine in medicine_expired:
        notifications.append({
            'type': 'expired',
            'color': 'orange',
            'message': f"Medicine '{medicine.name}' has expired on {medicine.exp_date} and will be removed."
        })
    medicine_expired.delete()  # Remove expired medicines from Medicine

    # Check Medicine for nearing expiration
    medicine_warnings = Medicine.objects.filter(exp_date__gt=current_date, exp_date__lte=notification_date)
    for medicine in medicine_warnings:
        # Check low stock condition
        if medicine.quantity <= (medicine.quantity / 3):  # Assuming 'initial_quantity' is the max stock
            notifications.append({
                'type': 'low_stock',
                'color': 'red',
                'message': f"Low stock for '{medicine.name}'. Only {medicine.quantity} left!"
            })
        else:
            supplier_name = medicine.supplier.name  # Access the supplier's name
            notifications.append({
                'type': 'expire',
                'color': 'blue',
                'message': f"Medicine '{medicine.name}' will expire on {medicine.exp_date}, supplied by {supplier_name}."
            })

    # Total notifications count
    total_notifications = len(notifications)

    # Fetch all pharmacies
    pharmacies = Pharmacy.objects.all()  # Get all pharmacy instances
    pharmacy_data = []

    for pharmacy in pharmacies:
        # Get all medicines for the current pharmacy in Pmedstock
        medicines = Pmedstock.objects.filter(pharmacy=pharmacy)
        
        # Calculate total stock and stock percentage
        total_stock = sum(medicine.stock for medicine in medicines)
        total_medicines_count = medicines.count()
        
        # Handle case where there are no medicines
        if total_medicines_count > 0:
            stock_percentage = (total_stock * 100) / (total_medicines_count * 100)  # Assuming max stock is 100 per medicine
        else:
            stock_percentage = 0

        # Append pharmacy data with calculated stock percentage
        pharmacy_data.append({
            'name': pharmacy.P_name,
            'total_stock': total_stock,
            'stock_percentage': stock_percentage,
        })

    # Fetch all suppliers and their medicines
    suppliers = Supplier.objects.all()
    supplier_data = []

    for supplier in suppliers:
        # Get all medicines for the current supplier
        medicines = Medicine.objects.filter(supplier=supplier)  # Assuming a ForeignKey relationship
        total_stock = sum(medicine.quantity for medicine in medicines)
        total_medicines_count = medicines.count()

        # Calculate stock percentage
        if total_medicines_count > 0:
            stock_percentage = (total_stock * 100) / (total_medicines_count * 100)  # Assuming max stock is 100 per medicine
        else:
            stock_percentage = 0

        # Append supplier data with calculated stock percentage
        supplier_data.append({
            'name': supplier.name,
            'total_stock': total_stock,
            'stock_percentage': stock_percentage,
        })

    return render(request, 'myapp/dashboard.html', {
        'total_medicines': total_medicines,
        'total_pharmacies': total_pharmacies,
        'total_suppliers': total_suppliers,
        'total_notifications': total_notifications,  # Pass the notification count
        'notifications': notifications,  # Pass the notification details
        'pharmacy_data': pharmacy_data,  # Pass the calculated pharmacy data
        'supplier_data': supplier_data,  # Pass the calculated supplier data
    })


def supplierdashboard(request):
    total_medicines = Medicine.objects.count()

    return render(request, 'myapp/supplierdashboard.html'), {
        'total_medicines' : total_medicines
    }


def message_view(request):
    # Fetch the count of unread messages
    unread_count = Message.objects.filter(is_read=False).count()

    return render(request, 'myapp/userhome.html', {
        'unread_count': unread_count,
        # Add other context variables as needed
    })


def userhome(request):
    # Get the logged-in pharmacy's name from the session
    logged_in_pharmacy_name = request.session.get('user_name')

    # Total counts for the dashboard
    total_medicines_count = Pmedstock.objects.count()
    pending_orders_count = Order.objects.filter(order_status='pending',pharmacy__P_name=logged_in_pharmacy_name).count()
    low_stock_level = Pharmacy.objects.filter(P_name=logged_in_pharmacy_name, stock_level='low').count()
    unread_message = Message.objects.filter(receiver_pharmacy=logged_in_pharmacy_name,is_read=False).count()
    orders = Order.objects.filter(pharmacy__P_name=logged_in_pharmacy_name).select_related('supplier', 'medicine')

    # Fetch other data
    data = Pmedstock.objects.all()

    return render(request, 'myapp/userhome.html', {
        'total_medicines_count': total_medicines_count,
        'pending_orders_count': pending_orders_count,
        'low_stock_level': low_stock_level,
        'unread_message': unread_message,  # Unread messages count for the logged-in pharmacy
        'orders': orders,  # Orders specific to the logged-in pharmacy
        'data': data,
    })


def sales_report(request):
    # Get current date and time for calculations
    now = timezone.now()
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = now - timezone.timedelta(days=now.weekday())  # Monday
    start_of_month = now.replace(day=1)

    # Aggregate sales data
    report_data = (
        Order.objects
        .select_related('pharmacy', 'medicine')  # Optimize queries by joining tables
        .filter(order_status='delivered')  # Only include delivered orders for the report
        .annotate(
            # Using total_price directly from Order model
            daily_sales_quantity=Sum('quantity', filter=Q(order_date__gte=start_of_today)),
            daily_sales_price=Sum('total_price', filter=Q(order_date__gte=start_of_today)),
            weekly_sales_quantity=Sum('quantity', filter=Q(order_date__gte=start_of_week)),
            weekly_sales_price=Sum('total_price', filter=Q(order_date__gte=start_of_week)),
            monthly_sales_quantity=Sum('quantity', filter=Q(order_date__gte=start_of_month)),
            monthly_sales_price=Sum('total_price', filter=Q(order_date__gte=start_of_month)),
        )
        .values(
            'pharmacy__P_name',  # Get the pharmacy name
            'medicine__serial_number',  # Get the medicine serial number
        )
        .order_by('pharmacy__P_name')  # Order by pharmacy name
    )

    return render(request, 'myapp/report.html', {'report_data': report_data, 'now': now})


def dashsupply(request):
    # Retrieve the supplier's ID from the session (logged-in user)
    supplier_id = request.session.get('supplier_id')

    if not supplier_id:
        # Handle the case where supplier_id is not found in the session
        return render(request, "myapp/loggin_view.html", {
            'message': "Supplier ID not found in session. Please log in again."
        })

    # Get the logged-in supplier's instance
    try:
        supplier = Supplier.objects.get(S_id=supplier_id)
    except Supplier.DoesNotExist:
        return render(request, "myapp/loggin_view.html", {
            'message': "Supplier not found. Please contact support."
        })

    # Total counts for the dashboard
    total_medicines_count = Medicine.objects.filter(supplier_id=supplier_id).count()
    total_pending_count = Order.objects.filter(order_status='pending', supplier_id=supplier_id).count()

    # Count unread messages specifically for the logged-in supplier
    total_notification = Message.objects.filter(
        receiver_pharmacy=supplier.name,  # Filter by the logged-in supplier's name
        is_read=False
    ).count()

    # Fetch orders data
    data = Order.objects.filter(supplier_id=supplier_id)

    # Render dashboard template with data
    return render(request, 'myapp/supplierdashboard.html', {
        'total_medicines_count': total_medicines_count,
        'total_pending_count': total_pending_count,
        'total_notification': total_notification,  # Unread message count for the logged-in supplier
        'data': data,
    })


@login_required
def supplier_view_message(request):
    # Get the logged-in supplier's name from session
    logged_in_supplier_name = request.session.get('user_name')  # Fetch 'user_name' from session

    if not logged_in_supplier_name:
        # Handle the case where 'user_name' is not found in the session
        return render(request, "myapp/loggin_view.html", {
            'message': "User name not found in session. Please log in again."
        })

    # Filter messages for the logged-in supplier
    data = Message.objects.filter(receiver_pharmacy=logged_in_supplier_name)

    return render(request, "myapp/supplier_view_message.html", {
        'data': data,
    })


def supplier_order_view(request):
    # Get the logged-in supplier's name from the session
    logged_in_supplier_name = request.session.get('user_name')

    if not logged_in_supplier_name:
        # Handle the case where the supplier name is not found in the session
        return render(request, "myapp/supplier_order_view.html", {
            'data': [],
            'message': "You need to log in to view your orders."
        })

    try:
        # Fetch the Supplier object using the name
        supplier = Supplier.objects.get(name=logged_in_supplier_name)
    except Supplier.DoesNotExist:
        # Handle the case where the supplier does not exist
        return render(request, "myapp/supplier_order_view.html", {
            'data': [],
            'message': "Supplier not found."
        })

    # Filter orders related to the supplier
    data = Order.objects.filter(supplier=supplier)

    return render(request, "myapp/supplier_order_view.html", {
        'data': data,
        'supplier_name': logged_in_supplier_name,
    })


def supply_list(request):
    # Fetch all suppliers from the Supplier table
    data = Supplier.objects.all()
    # Make sure context is a dictionary
    context = {
        'data': data,
    }
    return render(request, "myapp/supply_list.html", context)


def index(request):
    pharmacies = Pharmacy.objects.all()
    return render(request, 'myapp/index.html', {'data': pharmacies})


def orderdash(request):
    data = Order.objects.all()
    return render(request, "myapp/orderdash.html", {
        'data': data,
    })


def notification(request):
    notifications = Notification.objects.all()
    return render(request, 'myapp/notification.html', {'data': notifications})


def report(request):
    return render(request, "myapp/report.html")

def view(request):
    return render(request, "myapp/view.html")


def message(request):
    return render(request, "myapp/message.html")

def howitwork(request):
    return render(request, "myapp/howitwork.html")

def contact_us(request):
    return render(request, "myapp/contact_us.html")

def FAQs(request):
    return render(request, "myapp/FAQs.html")

def About_us(request):
    return render(request, "myapp/About_us.html")

def userdash(request):
    return render(request, "myapp/userdash.html")

def pharmacyordering(request):
    return render(request, "myapp/pharmacyordering.html")

def pharorder(request):
    return render(request, "myapp/pharorder.html")

def usernotification(request):
    return render(request, "myapp/usernotification.html")

def usersendmessage(request):
    return render(request, "myapp/usersendmessage.html")

def home(request):
    return render(request, "myapp/home.html")

def pharmaddmedicine(request):
    return render(request, "myapp/pharmaddmedicine.html")

def medicineview(request):
    return render(request, "myapp/medicineview.html")

def medicinedetails(request):
    return render(request, "myapp/medicinedetails.html")

def incame(request):
    return render(request, "myapp/incame.html")

def expences(request):
    return render(request, "myapp/expences.html")

def supplierdashboard(request):
    return render(request, "myapp/supplierd.html")

def supplierdashboard(request):
    return render(request, "myapp/supplierdashboard.html")

def message_view(request):
    return render(request, "myapp/userhome.html")

def resetpass(request):
    return render(request, "myapp/resetpass.html")
