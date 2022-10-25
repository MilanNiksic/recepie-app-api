from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recepie
from recepie import serializers


class RecepieViewSet(viewsets.ModelViewSet):

    serializer_class = serializers.RecepieSerializer
    queryset = Recepie.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-id')
