from django.core.exceptions import PermissionDenied
from braces.views import GroupRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy

from takeaway.forms import CheckoutForm, PiattoForm, OrdineForm, SogliaScontoForm
from takeaway.models import *


def clienti_group(user):
    return user.groups.filter(name='Clienti').exists()

def dipendenti_group(user):
    return user.groups.filter(name='Dipendenti').exists()


class PiattoDetail(DetailView):
    model = Piatto
    template_name = "takeaway/piatto/piatto_detail.html"


class PiattoListView(ListView):
    model = Piatto
    template_name = "takeaway/piatto/piatto_list.html"

    def get_queryset(self):
        queryset = Piatto.objects.all()

        portata = self.request.GET.get('portata')
        ingrediente = self.request.GET.get('ingrediente')

        if portata and portata != 'tutti':
            queryset = queryset.filter(portata=portata)

        if ingrediente and ingrediente != 'tutti':
            queryset = queryset.filter(ingredienti=ingrediente)

        return sorted(queryset, key=lambda p: p.portata_ordine)

    # Per mantenere selezionate le opzioni nel menu
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['portata_selezionata'] = self.request.GET.get('portata', 'tutti')
        context['ingrediente_selezionato'] = self.request.GET.get('ingrediente', 'tutti')
        return context


class PiattoCreate(GroupRequiredMixin, CreateView):
    group_required = ["Dipendenti"]
    model = Piatto
    form_class = PiattoForm
    template_name = "takeaway/piatto/piatto_create.html"
    success_url = reverse_lazy("takeaway:piatti")


class PiattoDelete(GroupRequiredMixin, DeleteView):
    group_required = ["Dipendenti"]
    model = Piatto
    success_url = reverse_lazy("takeaway:piatti")


class PiattoUpdate(GroupRequiredMixin, UpdateView):
    group_required = ["Dipendenti"]
    model = Piatto
    form_class = PiattoForm
    template_name = "takeaway/piatto/piatto_update.html"
    success_url = reverse_lazy("takeaway:piatti")


# Aggiunge un piatto al carrello
@user_passes_test(clienti_group)
def aggiungi_al_carrello(request, id_piatto):
    piatto = get_object_or_404(Piatto, id=id_piatto)
    carrello, created = Carrello.objects.get_or_create(cliente=request.user)

    # Se il piatto è già nel carrello -> incremento quantità
    piatto, created = PiattoCarrello.objects.get_or_create(carrello=carrello, piatto=piatto)
    if not created:
        piatto.quantita += 1
        piatto.save()

    return redirect("takeaway:carrello")


# Rimuove un piatto dal carrello
@user_passes_test(clienti_group)
def rimuovi_dal_carrello(request, id_piatto):
    piatto = get_object_or_404(Piatto, id=id_piatto)
    carrello = get_object_or_404(Carrello, cliente=request.user)

    PiattoCarrello.objects.filter(carrello=carrello, piatto=piatto).delete()

    return redirect("takeaway:carrello")


# Aggiorna quantità piatto nel carrello
@user_passes_test(clienti_group)
def aggiorna_nel_carrello(request, id_piatto):
    if request.method == "POST":
        piatto_carrello = get_object_or_404(PiattoCarrello, id=id_piatto, carrello__cliente=request.user)
        try:
            quantita = int(request.POST.get("quantita", 1))
            if quantita < 1:
                # Se la quantità inserita è <1, rimuovi il piatto dal carrello
                piatto_carrello.delete()
            else:
                piatto_carrello.quantita = quantita
                piatto_carrello.save()
        except ValueError:
            # Se non è un numero valido -> ignoro
            pass

    return redirect("takeaway:carrello")


# Mostra il carrello
@user_passes_test(clienti_group)
def visualizza_carrello(request):
    carrello, created = Carrello.objects.get_or_create(cliente=request.user)
    return render(request, "takeaway/carrello/carrello.html", {"carrello": carrello})


@user_passes_test(clienti_group)
def checkout(request):
    # Prendo il carrello dell'utente
    carrello = get_object_or_404(Carrello, cliente=request.user)
    piatti_carrello = PiattoCarrello.objects.filter(carrello=carrello)

    carta_fedelta, created = CartaFedelta.objects.get_or_create(cliente=request.user)
    soglia_sconto = SogliaSconto.objects.first()

    # Controllo se è possibile applicare lo sconto
    if carta_fedelta.punti >= soglia_sconto.punti_richiesti:
        sconto = soglia_sconto.valore_buono
        if sconto > carrello.totale():
            sconto = carrello.totale()
    else:
        sconto = 0

    if not piatti_carrello.exists():
        # Carrello vuoto
        return redirect('takeaway:piatti')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            ordine = form.save(commit=False) # Non salvo subito
            ordine.cliente = request.user
            ordine.sconto = sconto
            ordine.save()

            if sconto > 0:
                carta_fedelta.rimuovi_punti(soglia_sconto.punti_richiesti)

            # Copia piatti dal carrello all'ordine
            for piatto in piatti_carrello:
                PiattoOrdine.objects.create(
                    ordine=ordine,
                    piatto=piatto.piatto,
                    quantita=piatto.quantita,
                    prezzo_unitario=piatto.piatto.prezzo
                )

            # Svuota il carrello
            piatti_carrello.delete()

            return redirect('takeaway:checkout_success')
    else:
        form = CheckoutForm()

    totale = carrello.totale()
    totale_scontato = totale - sconto

    return render(request, 'takeaway/carrello/checkout.html', {
        'form': form,
        'piatti': piatti_carrello,
        'totale': totale,
        'sconto': sconto,
        'totale_scontato': totale_scontato
    })


@user_passes_test(clienti_group)
def checkout_success(request):
    return render(request, 'takeaway/carrello/checkout_success.html')


# Dettaglio ordine
class OrdineDetailView(GroupRequiredMixin, DetailView):
    group_required = ["Clienti", "Dipendenti"]
    model = Ordine
    template_name = 'takeaway/ordine/ordine_detail.html'
    context_object_name = 'ordine'


# Lista ordini
class OrdiniListView(GroupRequiredMixin, ListView):
    group_required = ["Clienti", "Dipendenti"]
    model = Ordine
    template_name = 'takeaway/ordine/ordine_list.html'
    context_object_name = 'ordini'

    def get_queryset(self):
        data = self.request.GET.get('data', 'futuri')
        stato = self.request.GET.get('stato', 'pending')

        print(data, stato)

        if self.request.user.groups.filter(name="Clienti").exists():
            # Se è un cliente -> mostro solo i suoi ordini
            queryset = Ordine.objects.filter(cliente=self.request.user)
        elif self.request.user.groups.filter(name="Dipendenti").exists():
            # Se è un dipendente -> mostro tutti gli ordini
            queryset = Ordine.objects.filter().order_by('orario_ritiro')
        else:
            raise PermissionDenied("Non hai accesso a questi ordini.")

        if data == 'futuri':
            queryset = queryset.filter(orario_ritiro__gt=timezone.now())
        elif data == 'passati':
            queryset = queryset.filter(orario_ritiro__lt=timezone.now())
        else:
            queryset = queryset.filter()

        if stato != 'tutti':
            queryset = queryset.filter(stato=stato)

        return queryset.order_by('orario_ritiro')

    # Per mantenere selezionate le opzioni nel menu
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['portata_selezionata'] = self.request.GET.get('data', 'futuri')
        context['stato_selezionato'] = self.request.GET.get('stato', 'pending')
        return context


class OrdineDelete(GroupRequiredMixin, DeleteView):
    group_required = ["Dipendenti"]
    model = Ordine
    success_url = reverse_lazy("takeaway:ordini")


class OrdineUpdate(GroupRequiredMixin, UpdateView):
    group_required = ["Dipendenti"]
    model = Ordine
    form_class = OrdineForm
    template_name = "takeaway/ordine/ordine_update.html"
    success_url = reverse_lazy("takeaway:ordini")

    def form_valid(self, form):
        ordine = form.save(commit=False)

        # se lo stato diventa 'completed' assegna punti
        if ordine.stato == "completed":
            punti = int(ordine.totale_scontato())  # 1 punto per ogni euro
            carta, created = CartaFedelta.objects.get_or_create(cliente=ordine.cliente)
            carta.aggiungi_punti(punti)

        ordine.save()
        return redirect("takeaway:ordini")


@user_passes_test(clienti_group)
def visualizza_carta_fedelta(request):
    carta_fedelta, created = CartaFedelta.objects.get_or_create(cliente=request.user)
    soglia_sconto = SogliaSconto.objects.first()
    punti_rimanenti = soglia_sconto.punti_richiesti - carta_fedelta.punti

    return render(request, "takeaway/carta_fedelta/carta_fedelta_detail.html", {"carta_fedelta": carta_fedelta,
                                                                                "soglia_sconto": soglia_sconto, "punti_rimanenti": punti_rimanenti})


# Dettaglio soglia sconto
@user_passes_test(dipendenti_group)
def visualizza_soglia_buono(request):
    soglia, created = SogliaSconto.objects.get_or_create()  # Unica soglia
    return render(request, 'takeaway/carta_fedelta/soglia_sconto_detail.html', {'soglia': soglia})


# Modifica soglia sconto
@user_passes_test(dipendenti_group)
def aggiorna_soglia_buono(request):
    soglia = SogliaSconto.objects.first()  # unica soglia

    if request.method == 'POST':
        form = SogliaScontoForm(request.POST)
        if form.is_valid():
            soglia.punti_richiesti = form.cleaned_data['punti_richiesti']
            soglia.valore_buono = form.cleaned_data['valore_buono']
            soglia.save()
            return redirect('takeaway:soglia_sconto')
    else:
        # Precompilo i campi
        form = SogliaScontoForm(initial={
            'punti_richiesti': soglia.punti_richiesti,
            'valore_buono': soglia.valore_buono
        })

    return render(request, 'takeaway/carta_fedelta/soglia_sconto_update.html', {'form': form})