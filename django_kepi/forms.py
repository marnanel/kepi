from django import forms
import django_kepi.models as kepi_models

class ObjectAdminForm(forms.ModelForm):

    class Meta:
        model = kepi_models.Object
        exclude = [
                ]
