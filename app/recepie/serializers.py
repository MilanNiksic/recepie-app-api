from rest_framework import serializers
from core.models import Recepie


class RecepieSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recepie
        fields = ['id', 'title', 'price', 'link']
        read_only = ['id']
