from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from recepie import views

router = DefaultRouter()
router.register('recepies', views.RecepieViewSet)
router.register('tags', views.TagViewSet)
router.register('ingridients', views.IngridientViewSet)

app_name = 'recepie'

urlpatterns = [
    path('', include(router.urls)),
]
