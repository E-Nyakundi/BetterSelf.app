from django.db.models import Sum
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from mpesa.services import get_mpesa_summary

from .models import FinancialGoal
from .forms import FinancialGoalForm


class FinanceDashboardView(LoginRequiredMixin, TemplateView):
    """Finance & Wealth app's own dashboard, mirroring Inventory's pattern.

    Separate from the main Accounts dashboard's Finance *card* (which
    shows a compact summary and links here for the full view).
    """
    template_name = "Finance_Wealth/finance_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        goals = FinancialGoal.objects.filter(user=user)
        context['total_goals'] = goals.count()
        context['total_target'] = goals.aggregate(total=Sum('target_amount'))['total'] or 0
        context['total_saved'] = goals.aggregate(total=Sum('current_amount'))['total'] or 0
        context['recent_goals'] = goals.order_by('-created_at')[:5]
        # M-Pesa is its own isolated app, but surfaced here as data — this
        # dashboard is the "larger Finance & Wealth" umbrella it lives under.
        context['mpesa'] = get_mpesa_summary(user)
        return context


class FinancialGoalListView(LoginRequiredMixin, ListView):
    model = FinancialGoal
    template_name = 'Finance_Wealth/financialgoal_list.html'
    context_object_name = 'goals'

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user)


class FinancialGoalCreateView(LoginRequiredMixin, CreateView):
    model = FinancialGoal
    form_class = FinancialGoalForm
    template_name = 'Finance_Wealth/financialgoal_form.html'
    success_url = reverse_lazy('financial-goal-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class FinancialGoalDetailView(LoginRequiredMixin, DetailView):
    model = FinancialGoal
    template_name = 'Finance_Wealth/financialgoal_detail.html'
    context_object_name = 'goal'

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user)


class FinancialGoalUpdateView(LoginRequiredMixin, UpdateView):
    model = FinancialGoal
    form_class = FinancialGoalForm
    template_name = 'Finance_Wealth/financialgoal_form.html'
    success_url = reverse_lazy('financial-goal-list')

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user)


class FinancialGoalDeleteView(LoginRequiredMixin, DeleteView):
    model = FinancialGoal
    template_name = 'Finance_Wealth/financialgoal_confirm_delete.html'
    success_url = reverse_lazy('financial-goal-list')

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user)