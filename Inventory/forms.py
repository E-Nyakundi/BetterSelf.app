from django import forms
from .models import Category, Item

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'icon', 'image', 'parent']
        widgets = {
            'icon': forms.RadioSelect(attrs={'class': 'category-icon-input'}),
            'image': forms.FileInput(attrs={
                'accept': 'image/*',
                'capture': 'environment',
                'class': 'category-image-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Accept user to filter categories
        self.user = user
        super().__init__(*args, **kwargs)
        if user:
            self.fields['parent'].queryset = Category.objects.filter(user=user)
        else:
            self.fields['parent'].queryset = Category.objects.none()
        self.fields['parent'].required = False
        self.fields['image'].required = False
        for name, field in self.fields.items():
            if name not in ('icon', 'image'):
                field.widget.attrs.setdefault('class', 'form-control')

    def clean_parent(self):
        parent = self.cleaned_data.get('parent')
        if parent and (not self.user or parent.user_id != self.user.id):
            raise forms.ValidationError("Choose one of your own categories.")
        return parent


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'image', 'category', 'date_acquired', 'condition', 'purpose', 'item_type']
        labels = {
            'item_type': 'Type',
        }
        widgets = {
            'date_acquired': forms.DateInput(attrs={'type': 'date'}),
            'condition': forms.Select(),
            'image': forms.FileInput(attrs={
                'accept': 'image/*',
                'capture': 'environment',
                'class': 'item-image-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Accept user to filter category options
        self.user = user
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
        else:
            self.fields['category'].queryset = Category.objects.none()
        self.fields['image'].required = False
        for name, field in self.fields.items():
            if name != 'image':
                field.widget.attrs.setdefault('class', 'form-control')

    def clean_category(self):
        category = self.cleaned_data.get('category')
        if category and (not self.user or category.user_id != self.user.id):
            raise forms.ValidationError("Choose one of your own categories.")
        return category
