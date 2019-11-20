from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
import kepi.trilby_api.forms as trilby_forms
import kepi.trilby_api.models as trilby_models
from kepi.bowler_pub.create import create

@admin.register(trilby_models.TrilbyUser)
class TrilbyUserAdmin(UserAdmin):

    fieldsets = (
            (None, {'fields': ('username', 'name', 'bio', 'email')}),
            ('Images', {'fields': ('avatar', 'header')}),
            )

    form = trilby_forms.UserForm

    def save_model(self, request, obj, form, change):

        if change:

            actor = obj.actor

            for field, value in form.cleaned_data.items():
                actor[field] = value

            actor.save()

        else:
            # A new TrilbyUser.
            # Create a new AcPerson and link them up.

            actor = {
                    'id': '@'+obj.get_username(),
                    'type': 'Person',
                    }

            obj.actor = create(
                    value=actor,
                    )

        super().save_model(request, obj, form, change)
