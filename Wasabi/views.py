from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from Wasabi.forms import CreaUtenteCliente, CreaUtenteDipendente


def homepage(request):
    return render(request, "home.html")


class ClienteCreateView(CreateView):
    form_class = CreaUtenteCliente
    template_name = "user_create.html"
    success_url = reverse_lazy("login")


class DipendenteCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "is_staff"
    form_class = CreaUtenteDipendente
    template_name = "user_create.html"
    success_url = reverse_lazy("login")

