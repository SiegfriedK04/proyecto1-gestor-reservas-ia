from django import forms

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
