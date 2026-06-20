from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import JournalEntry
from .forms import JournalEntryForm
from datetime import date
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin


class JournalView(LoginRequiredMixin, View):
    template_name = 'WellBeing/Journal.html'
    form_class = JournalEntryForm

    def get(self, request, journal_id=None):
        selected_date_str = request.GET.get('date', date.today().isoformat())
        try:
            selected_date = date.fromisoformat(selected_date_str)
        except ValueError:
            selected_date = date.today()
            selected_date_str = selected_date.isoformat()

        journal_instance = None
        if journal_id:
            journal_instance = get_object_or_404(JournalEntry, id=journal_id, user=request.user)
        
        form = self.form_class(instance=journal_instance)
        todays_journals = JournalEntry.objects.filter(days_date=selected_date, user=request.user)
        day_name = selected_date.strftime('%A')  # Full day name

        context = {
            'form': form,
            'day': day_name,
            'date': selected_date.strftime('%b. %d, %Y'),
            'todays_journals': todays_journals,
            'selected_date': selected_date_str,
        }
        return render(request, self.template_name, context)

    def post(self, request, journal_id=None):
        selected_date_str = request.GET.get('date', date.today().isoformat())
        try:
            selected_date = date.fromisoformat(selected_date_str)
        except ValueError:
            selected_date = date.today()
            selected_date_str = selected_date.isoformat()

        journal_instance = None
        if journal_id:
            journal_instance = get_object_or_404(JournalEntry, id=journal_id, user=request.user)

        # ✅ Include request.FILES here
        form = self.form_class(request.POST, request.FILES, instance=journal_instance)

        if form.is_valid():
            journal_obj = form.save(commit=False)

            if not journal_id:
                journal_obj.user = request.user  # Set user only for new entries

            journal_obj.days_date = selected_date  # Always set the selected date
            journal_obj.save()

            return redirect(f"{reverse('journal')}?date={selected_date_str}")

        todays_journals = JournalEntry.objects.filter(days_date=selected_date, user=request.user)
        day_name = selected_date.strftime('%A')  # Full day name

        context = {
            'form': form,
            'day': day_name,
            'date': selected_date.strftime('%b. %d, %Y'),
            'todays_journals': todays_journals,
            'selected_date': selected_date_str,
        }
        return render(request, self.template_name, context)

