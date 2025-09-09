from django.core.exceptions import PermissionDenied


def client_group(user):
    return user.groups.filter(name='Clienti').exists()

from braces.views import GroupRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy

from takeaway.forms import CheckoutForm, PiattoForm, OrdineForm
from takeaway.models import *


class PiattoDetail(DetailView):
    model = Piatto
    template_name = "takeaway/piatto_detail.html"


class PiattoListView(ListView):
    model = Piatto
    template_name = "takeaway/piatto_list.html"

    def get_queryset(self):
        queryset = Piatto.objects.all()

        portata = self.request.GET.get('portata')
        ingrediente = self.request.GET.get('ingrediente')

        if portata and portata != 'tutti':
            queryset = queryset.filter(portata=portata)

        if ingrediente and ingrediente != 'tutti':
            queryset = queryset.filter(ingredienti=ingrediente)

        return sorted(queryset, key=lambda p: p.portata_ordine)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['portata_selezionata'] = self.request.GET.get('portata', 'tutti')
        context['ingrediente_selezionato'] = self.request.GET.get('ingrediente', 'tutti')
        return context


class PiattoCreate(GroupRequiredMixin, CreateView):
    group_required = ["Dipendenti"]
    model = Piatto
    form_class = PiattoForm
    template_name = "takeaway/gestione_piatti/piatto_create.html"
    success_url = reverse_lazy("takeaway:piatti")


class PiattoDelete(GroupRequiredMixin, DeleteView):
    group_required = ["Dipendenti"]
    model = Piatto
    success_url = reverse_lazy("takeaway:piatti")


class PiattoUpdate(GroupRequiredMixin, UpdateView):
    group_required = ["Dipendenti"]
    model = Piatto
    form_class = PiattoForm
    template_name = "takeaway/gestione_piatti/piatto_update.html"
    success_url = reverse_lazy("takeaway:piatti")


# Aggiunge un piatto al carrello
@user_passes_test(client_group)
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
@user_passes_test(client_group)
def rimuovi_dal_carrello(request, id_piatto):
    piatto = get_object_or_404(Piatto, id=id_piatto)
    carrello = get_object_or_404(Carrello, cliente=request.user)

    PiattoCarrello.objects.filter(carrello=carrello, piatto=piatto).delete()

    return redirect("takeaway:carrello")


# Aggiorna quantità piatto nel carrello
@user_passes_test(client_group)
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
@user_passes_test(client_group)
def visualizza_carrello(request):
    carrello, created = Carrello.objects.get_or_create(cliente=request.user)
    return render(request, "takeaway/carrello/carrello.html", {"carrello": carrello})


@user_passes_test(client_group)
def checkout(request):
    # Prendo il carrello dell'utente
    carrello = get_object_or_404(Carrello, cliente=request.user)
    piatti_carrello = PiattoCarrello.objects.filter(carrello=carrello)

    if not piatti_carrello.exists():
        # Carrello vuoto
        return redirect('takeaway:piatti')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            ordine = form.save(commit=False)
            ordine.cliente = request.user
            ordine.save()

            # Copia piatti dal carrello all'ordine
            for item in piatti_carrello:
                PiattoOrdine.objects.create(
                    ordine=ordine,
                    piatto=item.piatto,
                    quantita=item.quantita,
                    prezzo_unitario=item.piatto.prezzo
                )

            # Svuota il carrello
            piatti_carrello.delete()

            return redirect('takeaway:checkout_success')
    else:
        form = CheckoutForm()

    return render(request, 'takeaway/carrello/checkout.html', {
        'form': form,
        'piatti': piatti_carrello
    })


@user_passes_test(client_group)
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
        if self.request.user.groups.filter(name="Clienti").exists():
            # Se è un cliente -> mostro solo i suoi ordini
            return Ordine.objects.filter(cliente=self.request.user).order_by('orario_ritiro')
        elif self.request.user.groups.filter(name="Dipendenti").exists():
            # Se è un dipendente -> mostro tutti gli ordini
            return Ordine.objects.filter().order_by('orario_ritiro')
        else:
            raise PermissionDenied("Non hai accesso a questi ordini.")


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