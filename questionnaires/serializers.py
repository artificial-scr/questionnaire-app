from rest_framework import serializers

from .models import Questionnaire
from .validation import validate_questionnaire


class QuestionnaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questionnaire
        fields = ['id', 'slug', 'title', 'data', 'created_at', 'updated_at']
        read_only_fields = ['slug', 'title', 'created_at', 'updated_at']

    def validate_data(self, data):
        errors = validate_questionnaire(data)
        if errors:
            raise serializers.ValidationError(errors)

        clash = Questionnaire.objects.filter(slug=data['id'])
        if self.instance is not None:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError([f"id: a questionnaire with id '{data['id']}' already exists"])
        return data
