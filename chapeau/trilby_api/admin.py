from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
import chapeau.trilby_api.forms as trilby_forms
import chapeau.trilby_api.models as trilby_models
from chapeau.kepi.create import create

@admin.register(trilby_models.TrilbyUser)
class TrilbyUserAdmin(UserAdmin):
    pass

#    form = trilby_forms.UserForm

    def save_model(self, request, obj, form, change):

        if not change:
            actor = {
                    'id': '@'+obj.get_username(),
                    'type': 'Person',
                    }

            obj.actor = create(
                    value=actor,
                    )

        super().save_model(request, obj, form, change)
