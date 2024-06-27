from django.core.management.base import BaseCommand, CommandParser
from users.models import User


class Command(BaseCommand):
    help = "Upgrade user to a superuser previlage"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--email",
            dest="email",
            help="Specifies the email address of app user to upgrade as the superuser.",
        )

    def handle(self, *args, **kwargs) -> None:
        email = kwargs.get("email")
        if email:
            try:
                user = User.objects.get(
                    email=email
                )
                user.is_superuser = True
                user.is_staff = True
                user.is_active = True
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully upgraded user {email} to superuser."
                    )
                )
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User {email} does not exist or not active or verified"))
        else:
            self.stdout.write(self.style.ERROR(f"No email address provided."))
