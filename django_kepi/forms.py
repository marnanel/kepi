from django import forms
import django_kepi.models as kepi_models

class IsLocalWidget(forms.MultiWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(
                *args,
                widgets = [
                    forms.CheckboxInput,
                    forms.TextInput,
                    ],
                **kwargs)

    def decompress(self, value):
        if value is None:
            return [False, '']
        else:
            return [True, value]

class ObjectAdminForm(forms.ModelForm):

    class Meta:
        model = kepi_models.Object
        fields = (
                'number',
                'remote_url',
                )
        widgets = {
                'number': forms.TextInput,
                'remote_url': IsLocalWidget,
                }



