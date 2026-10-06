from django.conf import settings
from django.db import models


class UserPreferences(models.Model):
    class Language(models.TextChoices):
        ENGLISH = "en", "English"
        FRENCH = "fr", "Français"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    language = models.CharField(
        max_length=2,
        choices=Language.choices,
        default=Language.ENGLISH,
    )

    def __str__(self) -> str:
        return f"{self.user} preferences"
