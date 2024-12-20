from django import forms
from .models import Pharmacy
from django.contrib.auth.models import User

class PharmacySignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")  # Password field with hiding

    class Meta:
        model = Pharmacy
        fields = ['P_name', 'contact_info', 'location', 'start_time', 'end_time', 'password']


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']




from .models import Medicine  # Import the correct model

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine  # Change this to Medicine
        fields = ['name', 'serial_number', 'exp_date', 'MFG_date', 'quantity', 'price']  # Ensure field names match the Medicine model
        widgets = {
            'exp_date': forms.DateInput(attrs={'type': 'date'}),
            'MFG_date': forms.DateInput(attrs={'type': 'date'}),
        }




        


    
