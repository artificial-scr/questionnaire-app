from django.core.exceptions import ValidationError
from django.db import models

from .validation import validate_questionnaire


class Questionnaire(models.Model):
    """A questionnaire whose full definition is stored as a JSON document.

    ``slug`` and ``title`` mirror ``data["id"]`` and ``data["title"]`` so they
    can be listed and searched without parsing the document.
    """

    slug = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=200)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def clean(self):
        errors = validate_questionnaire(self.data)
        if errors:
            raise ValidationError({'data': errors})
        if Questionnaire.objects.filter(slug=self.data['id']).exclude(pk=self.pk).exists():
            raise ValidationError({'data': f"A questionnaire with id '{self.data['id']}' already exists."})

    def save(self, *args, **kwargs):
        self.slug = self.data['id']
        self.title = self.data['title']
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
