from django.urls import path

from .views import *

app_name = "takeaway"

urlpatterns = [
    path("piatto/<int:pk>", PiattoDetail.as_view(), name="piatto"),
    path("piatti/", PiattoListView.as_view(), name="piatti"),
    path("carrello/", visualizza_carrello, name="carrello"),
    path("carrello/aggiungi/<int:id_piatto>", aggiungi_al_carrello, name="carrello_add"),
    path("carrello/rimuovi/<int:id_piatto>", rimuovi_dal_carrello, name="carrello_remove"),
    path("carrello/aggiorna/<int:id_piatto>", aggiorna_nel_carrello, name="carrello_update"),
    path("carrello/checkout", checkout, name="checkout"),
    path('carrello/checkout_success/', checkout_success, name='checkout_success'),
    path('ordini/', OrdiniListView.as_view(), name='ordini'),
    path('ordine/<int:pk>/', OrdineDetailView.as_view(), name='ordine'),
    path("aggiungi_piatto", PiattoCreate.as_view(), name="piatto_create"),
    path("rimuovi_piatto/<int:pk>", PiattoDelete.as_view(), name="piatto_delete"),
    path("modifica_piatto/<int:pk>", PiattoUpdate.as_view(), name="piatto_update"),
]