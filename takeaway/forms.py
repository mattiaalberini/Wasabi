from django import forms
from .models import Ordine, Piatto


class CheckoutForm(forms.ModelForm):
    orario_ritiro = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label="Orario di ritiro"
    )

    class Meta:
        model = Ordine
        fields = ['orario_ritiro']


class PiattoForm(forms.ModelForm):
    class Meta:
        model = Piatto
        fields = ["nome", "descrizione", "prezzo", "portata", "ingredienti", "foto"]

    def clean_prezzo(self):
        prezzo = self.cleaned_data.get('prezzo')
        if prezzo < 0:
            raise forms.ValidationError("Il prezzo non può essere negativo.")
        return prezzo


class OrdineForm(forms.ModelForm):
    class Meta:
        model = Ordine
        fields = ["stato"]