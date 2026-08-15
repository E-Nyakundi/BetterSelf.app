from django.db.models import Q
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Category, Item
from .forms import CategoryForm, ItemForm

# CATEGORY VIEWS
class InventoryDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "Inventory/inventory_dashboard.html"
    form_class = CategoryForm
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['total_items'] = Item.objects.filter(user=user).count()
        context['total_categories'] = Category.objects.filter(user=user).count()
        context['recent_items'] = Item.objects.filter(user=user).select_related('category').order_by('-date_acquired')[:5]
        return context
    
    
class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'Inventory/category_form.html'
    success_url = reverse_lazy('category-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # Pass user to filter parent queryset
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'Inventory/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).select_related('parent').order_by('parent__id', 'name')


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'Inventory/category_confirm_delete.html'
    success_url = reverse_lazy('category-list')

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)


# ITEM VIEWS

class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = 'Inventory/item_form.html'
    success_url = reverse_lazy('item-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ItemListView(LoginRequiredMixin, ListView):
    model = Item
    template_name = 'Inventory/item_list.html'
    context_object_name = 'items'

    def get_queryset(self):
        queryset = Item.objects.filter(user=self.request.user).select_related('category')
        query = self.request.GET.get('q', '').strip()
        category_id = self.request.GET.get('category', '').strip()
        condition = self.request.GET.get('condition', '').strip()
        item_type = self.request.GET.get('item_type', '').strip()

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(purpose__icontains=query)
                | Q(item_type__icontains=query)
                | Q(category__name__icontains=query)
            )
        if category_id:
            queryset = queryset.filter(category_id=category_id, category__user=self.request.user)
        if condition:
            queryset = queryset.filter(condition=condition)
        if item_type:
            queryset = queryset.filter(item_type__icontains=item_type)

        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(user=self.request.user).order_by('parent__id', 'name')
        context['condition_choices'] = Item.CONDITION_CHOICES
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
            'category': self.request.GET.get('category', ''),
            'condition': self.request.GET.get('condition', ''),
            'item_type': self.request.GET.get('item_type', ''),
        }
        return context


class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item
    template_name = 'Inventory/item_detail.html'
    context_object_name = 'item'

    def get_queryset(self):
        return Item.objects.filter(user=self.request.user).select_related('category')


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = 'Inventory/item_form.html'
    success_url = reverse_lazy('item-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)


class ItemDisposeView(LoginRequiredMixin, DeleteView):
    model = Item
    template_name = 'Inventory/item_confirm_dispose.html'
    success_url = reverse_lazy('item-list')

    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)
