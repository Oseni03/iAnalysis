from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import Database, Message
from .forms import ChatForm, DatabaseForm
# from .utils import get_elasticsearch_agent, get_db_agent
# from .services import secrets

# Create your views here.
class DashboardView(LoginRequiredMixin, ListView):
    model = Database
    template_name = "dashboard/dashboard.html"
    context_object_name = "databases"
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user=request.user)
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["form"] = DatabaseForm()
        return context
    
    def post(self, request, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        form = DatabaseForm(request.POST)
        if form.is_valid():
            form.save(request.user)
            messages.success(request, "Database added successfully!")
        else:
            for error in form.errors.values():
                messages.info(request, error)
            context["form"] = form
        return render(request, self.template_name, context)


@login_required
def chat(reauest, pk):
    db = get_object_or_404(Database, id=pk, user=request.user)
    form = ChatForm()
    
    if request.method == "POST":
        form = ChatForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data["message"]
            model = form.cleaned_data["model"]
            
            identifier = generate_identifier(request.user, db)
            
            if identifier not in request.session:
                username, password = secrets.get_secret_value(identifier)
                conn_str = db.conn_str(username, password)
                
                if db.protocol == Database.ProtocolType.ELASTIC_SEARCH:
                    agent = get_elasticsearch_agent(conn_str, model, db.tbls)
                else:
                    agent = get_db_agent(conn_str, model, db.tbls)
                request.session[identifier] = agent
            else:
                agent = request.session.get(identifier)
            
            response = agent.run(query)
            result = response["result"]
            
            Message.objects.create(db=db, msg=query) # save user query to the database
            Message.objects.create(
                db=db, 
                msg=result, 
                sql_query=response["intermediate_steps"][-2],
                is_ai=True
            ) # save ai response and sql to the database 
            
            return JsonResponse({"query": query, "result": result})
        else:
            return JsonResponse({"errors": form.errors.values()})
            
    context = {
        "form": form,
        "messages": Message.objects.filter(db=db)
    }
    return render(request, "dashboard/partial/_chat.html", context)