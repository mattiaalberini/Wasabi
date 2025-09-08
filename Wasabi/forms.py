from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group


class CreaUtenteCliente(UserCreationForm):
    def save(self, commit=True):
        user = super().save(commit) # Ottengo un riferimento all'utente
        g = Group.objects.get(name='Clienti') # Cerco il gruppo
        g.user_set.add(user) # Aggiungo l'utente al gruppo
        return user

class CreaUtenteDipendente(UserCreationForm):
    def save(self, commit=True):
        user = super().save(commit)  # Ottengo un riferimento all'utente
        g = Group.objects.get(name='Dipendenti')  # Cerco il gruppo
        g.user_set.add(user)  # Aggiungo l'utente al gruppo
        return user