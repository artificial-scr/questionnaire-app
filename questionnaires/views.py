import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets
from rest_framework.decorators import action

from .models import Questionnaire
from .serializers import QuestionnaireSerializer
from .validation import load_schema


class QuestionnaireViewSet(viewsets.ModelViewSet):
    queryset = Questionnaire.objects.all()
    serializer_class = QuestionnaireSerializer

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Download the questionnaire document as a .json file."""
        questionnaire = self.get_object()
        response = HttpResponse(
            json.dumps(questionnaire.data, indent=2, ensure_ascii=False),
            content_type='application/json',
        )
        response['Content-Disposition'] = f'attachment; filename="{questionnaire.slug}.json"'
        return response


def schema_view(request):
    return JsonResponse(load_schema())


def questionnaire_list(request):
    return render(request, 'questionnaires/list.html', {
        'questionnaires': Questionnaire.objects.all(),
    })


def builder(request, pk=None):
    questionnaire = get_object_or_404(Questionnaire, pk=pk) if pk is not None else None
    return render(request, 'questionnaires/builder.html', {
        'questionnaire': questionnaire,
        # Explicit values so a new questionnaire serialises as null, not "".
        'pk': questionnaire.pk if questionnaire else None,
        'data': questionnaire.data if questionnaire else None,
    })
