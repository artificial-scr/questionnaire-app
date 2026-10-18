from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('questionnaires', views.QuestionnaireViewSet)

urlpatterns = [
    path('', views.questionnaire_list, name='questionnaire-list-page'),
    path('new/', views.builder, name='builder-new'),
    path('<int:pk>/edit/', views.builder, name='builder-edit'),
    path('api/', include(router.urls)),
    path('api/schema/questionnaire-1.0.json', views.schema_view, name='questionnaire-schema'),
]
