from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.views.generic import View
from django.utils.decorators import method_decorator

from .models import Data, Message
from .decorators import require_HTMX
from .forms import ChatForm, DatabaseForm, APIForm
from . import tasks


# Create your views here.
class DashboardView(LoginRequiredMixin, View):
    template_name = "dashboard/dashboard.html"
    
    def get(self, request, *args, **kwargs):
        context = {}
        context["databases"] = Data.objects.database().filter(user=request.user)
        context["apis"] = Data.objects.api().filter(user=request.user)
        return render(request, self.template_name, context)
    

@login_required
@require_HTMX
def chat(request, pk):
    data = get_object_or_404(Data, id=pk, user=request.user)
    form = ChatForm()
    
    if request.method == "POST":
        form = ChatForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data["message"]
            model = form.cleaned_data["model"]
            
            tasks.return_query_resp.delay(query, user.id, data.id, model)
            
            msg = Message.objects.create(source=data, text=query) # save user query to the database
            
            return render(request, "dashboard/partials/_msg.html", {"msg": msg})
        else:
            for error in forms.errors.values():
                messages.error(request, error)
            
    context = {
        "form": form,
        "messages": Message.objects.filter(source=data),
        "data": data
    }
    return render(request, "dashboard/partial/_chat.html", context)


@method_decorator(require_HTMX, name="dispatch")
class AddDataView(View):
    def get(self, request, data_type, *args, **kwargs):
        context = {}
        if data_type == "db":
            context["form"] = DatabaseForm()
            context["data_type"] = "Database"
        elif data_type == "api":
            context["form"] = APIForm()
            context["data_type"] = "API"
        return render(request, "dashboard/partials/_data_form.html", context)
    
    def post(self, request, data_type, *args, **kwargs):
        context = {}
        if data_type == "db":
            form = DatabaseForm(request.POST)
        elif data_type == "api":
            form = APIForm(request.POST)
        
        if form.is_valid():
            data = form.save(request.user)
            messages.success(request, "Data source added successfully!")
            return redirect("dashboard:data_chat", args=(data.id,))
        else:
            for error in form.errors.values():
                messages.info(request, error)
            context["form"] = form
            if data_type == "db":
                context["data_type"] = "Database"
            elif data_type == "api":
                context["data_type"] = "API"
        return render(request, "dashboard/partials/_data_form.html", context)
