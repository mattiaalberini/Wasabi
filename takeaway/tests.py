from django.test import TestCase

from takeaway.forms import PiattoForm
from takeaway.models import Piatto


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
            "descrizione": "Spaghetti in brodo",
            "prezzo": 4.00,
            "portata": "primo",
            "ingredienti": "carne"
        }

        form = PiattoForm(data=form_data)
        self.assertTrue(form.is_valid())