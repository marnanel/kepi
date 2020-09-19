from django import forms

class UserForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        if 'instance' in kwargs:
            actor = kwargs['instance'].actor

            if 'initial' not in kwargs:
                kwargs['initial'] = {}

            for field in [
                    'name',
                    'bio',
                    'avatar',
                    'header',
                    ]:
                kwargs['initial'][field] = actor[field]

        super().__init__(*args, **kwargs)

    name = forms.CharField(
            max_length = 256,
            required = False,
            )

    bio = forms.CharField(
            max_length = 2048,
            widget = forms.Textarea,
            required = False,
            )

    avatar = forms.ImageField(
            required = False,
            )

    header = forms.ImageField(
            required = False,
            )
