from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model

from users.forms import UserChangeForm, UserCreationForm

from contributors.models import Contributor
from consumers.models import Consumer


User = get_user_model()


class ContributorInline(admin.StackedInline):
    model = Contributor
    can_delete = False
    verbose_name_plural = 'Contributors'


class ConsumerInline(admin.StackedInline):
    model = Consumer
    can_delete = False
    verbose_name_plural = 'Consumers'


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (
        ("User", {"fields": ("name", "dob", "picture", "about_me", "terms_accepted", "otp", "activation_key", "applied_contributor", "approved_contributor")}),
    ) + auth_admin.UserAdmin.fieldsets
    list_display = ["username", "name", "first_name", "last_name", "email", "applied_contributor", "approved_contributor"]
    search_fields = ["name", "first_name", "last_name", "email"]

    inlines = [ContributorInline, ConsumerInline]


admin.site.register(Contributor)
admin.site.register(Consumer)
