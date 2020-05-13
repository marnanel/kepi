from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
import kepi.trilby_api.forms as trilby_forms
import kepi.trilby_api.models as trilby_models

@admin.register(trilby_models.LocalPerson)
class LocalPersonAdmin(admin.ModelAdmin):

    fieldsets = (
            (None, {'fields': ('local_user', 'display_name', 'note',)}),
            ('Defaults', {'fields': ('default_visibility', 'default_sensitive')}),
            ('Crypto', {'fields': ('publicKey', 'privateKey')}),
            ('Images', {'fields': ('icon_image', 'header_image')}),
            ('Flags', {'fields': ('auto_follow', 'locked', 'bot')}),
            )

    #form = trilby_forms.UserForm

@admin.register(trilby_models.RemotePerson)
class RemotePersonAdmin(admin.ModelAdmin):
    pass

@admin.register(trilby_models.Status)
class StatusAdmin(admin.ModelAdmin):
    pass
