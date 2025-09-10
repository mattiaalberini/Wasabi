from django import forms
from django.utils import timezone

from .models import Ordine, Piatto


class CheckoutForm(forms.ModelForm):
    orario_ritiro = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}), label="Orario di ritiro")

    class Meta:
        model = Ordine
        fields = ['orario_ritiro']

    def clean_orario_ritiro(self):
        orario = self.cleaned_data.get('orario_ritiro')
        if orario < timezone.now():
            raise forms.ValidationError("Non puoi scegliere una data/ora nel passato.")
        return orario


class PiattoForm(forms.ModelForm):
    class Meta:
        model = Piatto
        fields = ["nome", "descrizione", "prezzo", "portata", "ingredienti", "foto"]

    def clean_nome(self):
        nome = self.cleaned_data.get('nome')
        existing_piatto = Piatto.objects.filter(nome=nome)

        if existing_piatto:
            raise forms.ValidationError("Piatto già presente nel menu.")
        return nome

    def clean_prezzo(self):
        prezzo = self.cleaned_data.get('prezzo')
        if prezzo < 0:
            raise forms.ValidationError("Il prezzo non può essere negativo.")
        return prezzo


class OrdineForm(forms.ModelForm):
    class Meta:
        model = Ordine
        fields = ["stato"]


class SogliaScontoForm(forms.Form):
    punti_richiesti = forms.IntegerField(min_value=0, label="Punti richiesti")
    valore_buono = forms.DecimalField(min_value=0, max_digits=6, decimal_places=2, label="Valore buono (€)")