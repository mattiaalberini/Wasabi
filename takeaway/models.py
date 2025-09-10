import os

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

ORDINE_PORTATA = {
        'antipasto': 1,
        'primo': 2,
        'secondo': 3,
        'dessert': 4,
    }

class Piatto(models.Model):
    PORTATA_CHOICES = [
        ('antipasto', 'Antipasto'),
        ('primo', 'Primo'),
        ('secondo', 'Secondo'),
        ('dessert', 'Dessert'),
    ]

    INGREDIENTI_CHOICES = [
        ('carne', 'Carne'),
        ('pesce', 'Pesce'),
        ('vegano', 'Vegano'),
        ('vegetariano', 'Vegetariano'),
    ]

    nome = models.CharField(max_length=100)
    descrizione = models.TextField()
    prezzo = models.DecimalField(max_digits=6, decimal_places=2)
    portata = models.CharField(max_length=20, choices=PORTATA_CHOICES, default='primo')
    ingredienti = models.CharField(max_length=20, choices=INGREDIENTI_CHOICES, default='carne')
    foto = models.ImageField(upload_to='piatti/', blank=True, null=True)

    def __str__(self):
        return f"{self.nome} - {self.portata} ({self.prezzo} €)"

    class Meta:
        verbose_name_plural = "Piatti"

    @property
    def portata_ordine(self):
        return ORDINE_PORTATA[self.portata]

    # Rimozione foto
    def save(self, *args, **kwargs):
        # Se l'oggetto esiste già
        try:
            old_instance = Piatto.objects.get(pk=self.pk)
            if old_instance.foto and old_instance.foto != self.foto:
                if os.path.isfile(old_instance.foto.path):
                    os.remove(old_instance.foto.path)
        except Piatto.DoesNotExist:
            pass  # Nuovo oggetto -> niente da cancellare

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Elimina la foto al momento del delete
        if self.foto and os.path.isfile(self.foto.path):
            os.remove(self.foto.path)
        super().delete(*args, **kwargs)


class Carrello(models.Model):
    cliente = models.OneToOneField(User, on_delete=models.CASCADE)  # Un carrello per cliente

    def totale(self):
        return sum(piatto.subtotale() for piatto in self.piatti.all())

    def __str__(self):
        return f"Carrello di {self.cliente.username}"


class PiattoCarrello(models.Model):
    carrello = models.ForeignKey(Carrello, related_name="piatti", on_delete=models.CASCADE)
    piatto = models.ForeignKey(Piatto, on_delete=models.CASCADE)
    quantita = models.PositiveIntegerField(default=1)

    def subtotale(self):
        return self.piatto.prezzo * self.quantita


class Ordine(models.Model):
    STATUS_CHOICES = [
        ('pending', 'In attesa'),
        ('completed', 'Completato'),
        ('cancelled', 'Cancellato'),
    ]

    cliente = models.ForeignKey(User, on_delete=models.CASCADE)
    orario_ritiro = models.DateTimeField()
    stato = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    creato_il = models.DateTimeField(auto_now_add=True)
    sconto = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    def totale(self):
        return sum(piatto.subtotale() for piatto in self.piatti.all())

    def totale_scontato(self):
        return sum(piatto.subtotale() for piatto in self.piatti.all()) - self.sconto

    def __str__(self):
        return f"Ordine #{self.id} di {self.cliente.username}"

    def clean(self):
        # Se l'ordine è già salvato e non era più "pending"
        if self.pk:
            stato_originale = Ordine.objects.get(pk=self.pk).stato
            if stato_originale != "pending" and self.stato != stato_originale:
                raise ValidationError("Lo stato non può essere più modificato.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Fa scattare clean() prima di salvare
        super().save(*args, **kwargs)


class PiattoOrdine(models.Model):
    ordine = models.ForeignKey(Ordine, related_name="piatti", on_delete=models.CASCADE)
    piatto = models.ForeignKey(Piatto, on_delete=models.CASCADE)
    quantita = models.PositiveIntegerField(default=1)
    prezzo_unitario = models.DecimalField(max_digits=6, decimal_places=2) # Anche se cambia il prezzo del piatto, nell'ordine rimane uguale

    def subtotale(self):
        return self.prezzo_unitario * self.quantita

    def __str__(self):
        return f"{self.quantita} × {self.piatto.nome} (Ordine #{self.ordine.id})"


class CartaFedelta(models.Model):
    cliente = models.OneToOneField(User, on_delete=models.CASCADE, related_name="carta_fedelta")
    punti = models.PositiveIntegerField(default=0)

    def aggiungi_punti(self, valore):
        self.punti += valore
        self.save()

    def rimuovi_punti(self, valore):
        self.punti -= valore
        self.save()

    def __str__(self):
        return f"Carta {self.cliente.username} - {self.punti} punti"


class SogliaSconto(models.Model):
    punti_richiesti = models.PositiveIntegerField(default=100)
    valore_buono = models.DecimalField(max_digits=6, decimal_places=2, default=5)

    def __str__(self):
        return f"{self.punti_richiesti} punti -> Buono da €{self.valore_buono}"