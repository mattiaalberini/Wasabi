from django import forms
from .models import Ordine

class CheckoutForm(forms.ModelForm):
    orario_ritiro = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label="Orario di ritiro"
    )

    class Meta:
        model = Ordine
        fields = ['orario_ritiro']
