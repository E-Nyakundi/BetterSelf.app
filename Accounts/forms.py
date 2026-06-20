from django import forms

from .models import Profile


class ProfileForm(forms.ModelForm):
    MAX_IMAGE_SIZE = 2 * 1024 * 1024
    ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}

    class Meta:
        model = Profile
        fields = ['profile_img', 'email', 'title']
        labels = {
            'profile_img': 'Profile image',
            'title': 'Profile title',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def clean_profile_img(self):
        image = self.cleaned_data.get('profile_img')
        if not image:
            return image

        if image.size > self.MAX_IMAGE_SIZE:
            raise forms.ValidationError("Profile image must be 2MB or smaller.")

        content_type = getattr(image, 'content_type', None)
        if content_type and content_type not in self.ALLOWED_CONTENT_TYPES:
            raise forms.ValidationError("Upload a JPEG, PNG, WebP, or GIF image.")

        return image
