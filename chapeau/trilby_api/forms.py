from django import forms

class UserForm(forms.ModelForm):
    class Meta:
        fields = [
                'email',
                ]


