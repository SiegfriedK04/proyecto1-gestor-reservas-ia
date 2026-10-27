from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("phone", "preferred_resource", "default_repeat_weeks")
        labels = {
            "phone": "Teléfono",
            "preferred_resource": "Recurso preferido",
            "default_repeat_weeks": "Semanas de repetición predeterminadas",
        }
        widgets = {
            "phone": forms.TextInput(attrs={"placeholder": "+507 6000-0000"}),
            "default_repeat_weeks": forms.NumberInput(attrs={"min": 0, "max": 12}),
        }

    def clean_default_repeat_weeks(self):
        value = self.cleaned_data["default_repeat_weeks"]
        if value > 12:
            raise forms.ValidationError("No se pueden preseleccionar más de 12 semanas.")
        return value


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label="Correo electrónico", required=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")
        labels = {
            "username": "Nombre de usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo electrónico.")
        return email
