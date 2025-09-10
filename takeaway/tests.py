from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.urls import reverse

from takeaway.forms import PiattoForm
from takeaway.models import Piatto, SogliaSconto, Carrello, PiattoCarrello, CartaFedelta, Ordine, PiattoOrdine


# Aggiunta piatto
class PiattoFormTest(TestCase):
    def setUp(self):
        self.piatto = Piatto.objects.create(
            nome = "Ramen",
            descrizione = "Spaghetti in brodo",
            prezzo = 12.50,
            portata = "primo",
            ingredienti = "carne"
        )

    # Piatto duplicato
    def test_nome_piatto_duplicato(self):
        form_data = {
            "nome": "Ramen",
            "descrizione": "Spaghetti in brodo",
            "prezzo": 12.00,
            "portata": "primo",
            "ingredienti": "carne"
        }

        form = PiattoForm(data=form_data)
        self.assertFalse(form.is_valid())

    # Prezzo negativo
    def test_prezzo_piatto_negativo(self):
        form_data = {
            "nome": "Sushi",
            "descrizione": "Pesce fresco",
            "prezzo": -4.00,
            "portata": "secondo",
            "ingredienti": "pesce"
        }

        form = PiattoForm(data=form_data)
        self.assertFalse(form.is_valid())

    # Piatto valido
    def test_piatto_valido(self):
        form_data = {
            "nome": "Sushi",
            "descrizione": "Pesce fresco",
            "prezzo": 4.00,
            "portata": "secondo",
            "ingredienti": "pesce"
        }

        form = PiattoForm(data=form_data)
        self.assertTrue(form.is_valid())


# Checkout
class CheckoutTest(TestCase):
    def setUp(self):
        # Utente
        gruppo_clienti, created = Group.objects.get_or_create(name='Clienti')
        self.user = User.objects.create_user(username='cliente', password='prova123')
        self.user.groups.add(gruppo_clienti)
        self.client.login(username='cliente', password='prova123')

        # Piatti
        self.piatto1 = Piatto.objects.create(nome="Ramen", descrizione="Spaghetti in brodo",
            prezzo=12.50, portata="primo", ingredienti="carne"
        )
        self.piatto2 = Piatto.objects.create(nome="Sushi", descrizione="Pesce fresco",
            prezzo=4.00, portata="secondo", ingredienti="pesce"
        )

        # Soglia sconto
        self.soglia = SogliaSconto.objects.create(punti_richiesti=100, valore_buono=5)

        # Carrello
        self.carrello = Carrello.objects.create(cliente=self.user)
        PiattoCarrello.objects.create(carrello=self.carrello, piatto=self.piatto1, quantita=1)
        PiattoCarrello.objects.create(carrello=self.carrello, piatto=self.piatto2, quantita=2)

    # Niente sconto applicato
    def test_checkout_senza_sconto(self):
        # Carta fedeltà con pochi punti
        CartaFedelta.objects.create(cliente=self.user, punti=50)

        response = self.client.post(reverse('takeaway:checkout'), data={
            'orario_ritiro': '2025-09-11T12:00'
        })

        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertRedirects(response, reverse('takeaway:checkout_success'))

        ordine = Ordine.objects.get(cliente=self.user)
        self.assertEqual(PiattoOrdine.objects.filter(ordine=ordine).count(), 2)  # Numero piatti
        self.assertFalse(PiattoCarrello.objects.filter(carrello=self.carrello).exists())  # Carrello vuoto

        self.assertEqual(ordine.sconto, 0) # Niente sconto

    # Sconto applicato
    def test_checkout_con_sconto(self):
        # Carta fedeltà con punti sufficienti
        CartaFedelta.objects.create(cliente=self.user, punti=150)

        response = self.client.post(reverse('takeaway:checkout'), data={
            'orario_ritiro': '2025-09-11T12:00'
        })

        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertRedirects(response, reverse('takeaway:checkout_success'))

        ordine = Ordine.objects.get(cliente=self.user)
        self.assertEqual(PiattoOrdine.objects.filter(ordine=ordine).count(), 2)  # Numero piatti
        self.assertFalse(PiattoCarrello.objects.filter(carrello=self.carrello).exists())  # Carrello vuoto

        self.assertEqual(ordine.sconto, self.soglia.valore_buono) # Sconto applicato

        # Verifico che i punti siano stati rimossi dalla carta fedeltà
        carta = CartaFedelta.objects.get(cliente=self.user)
        self.assertEqual(carta.punti, 150 - self.soglia.punti_richiesti)

    # Carrello vuoto
    def test_checkout_carrello_vuoto(self):
        # Svuoto il carrello
        PiattoCarrello.objects.all().delete()

        response = self.client.post(reverse('takeaway:checkout'), data={
            'orario_ritiro': '2025-09-11T12:00'
        })

        # Deve fare redirect al menu perché carrello vuoto
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertRedirects(response, reverse('takeaway:piatti'))


# Aggiunta piatto diversi gruppi
class PiattoCreateTest(TestCase):
    def setUp(self):
        # Utenti
        gruppo_clienti, created = Group.objects.get_or_create(name='Clienti')
        gruppo_dipendenti, created = Group.objects.get_or_create(name='Dipendenti')
        self.cliente = User.objects.create_user(username='cliente', password='prova123')
        self.cliente.groups.add(gruppo_clienti)

        self.dipendente = User.objects.create_user(username='dipendente', password='prova123')
        self.dipendente.groups.add(gruppo_dipendenti)

    # Dipendente può aggiungere piatto
    def test_dipendente_aggiunge_piatto(self):
        self.client.login(username='dipendente', password='prova123')

        response = self.client.post(reverse('takeaway:piatto_create'), data={
            "nome": "Ramen",
            "descrizione": "Spaghetti in brodo",
            "prezzo": 12.00,
            "portata": "primo",
            "ingredienti": "carne"
        })

        self.assertEqual(response.status_code, 302) # Redirect
        self.assertRedirects(response, reverse('takeaway:piatti'))
        self.assertTrue(Piatto.objects.filter(nome='Ramen').exists()) # Piatto creato

    # Cliente non può aggiungere piatto
    def test_cliente_non_aggiunge_piatto(self):
        self.client.login(username='cliente', password='prova123')

        response = self.client.post(reverse('takeaway:piatto_create'), data={
            "nome": "Ramen",
            "descrizione": "Spaghetti in brodo",
            "prezzo": 12.00,
            "portata": "primo",
            "ingredienti": "carne"
        })

        self.assertEqual(response.status_code, 302) # Redirect
        self.assertIn(reverse('login'), response.url) # Reindirizzamento al login
        self.assertFalse(Piatto.objects.filter(nome='Ramen').exists()) # Piatto non creato

    # Utente non loggato non può aggiungere piatto
    def test_utente_non_loggato_non_aggiunge_piatto(self):
        self.client.logout()

        response = self.client.post(reverse('takeaway:piatto_create'), data={
            "nome": "Ramen",
            "descrizione": "Spaghetti in brodo",
            "prezzo": 12.00,
            "portata": "primo",
            "ingredienti": "carne"
        })

        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertIn(reverse('login'), response.url)  # Reindirizzamento al login
        self.assertFalse(Piatto.objects.filter(nome='Ramen').exists())  # Piatto non creato