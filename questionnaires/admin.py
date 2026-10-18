from django.contrib import admin

from .models import Questionnaire


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'updated_at']
    search_fields = ['title', 'slug']
    readonly_fields = ['slug', 'title', 'created_at', 'updated_at']
