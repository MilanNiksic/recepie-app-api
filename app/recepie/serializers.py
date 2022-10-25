from rest_framework import serializers
from core.models import Recepie


class RecepieSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recepie
        fields = ['id', 'title', 'time_minutes', 'price', 'link']
        read_only = ['id']


class RecepieDetailSerializer(RecepieSerializer):

    class Meta(RecepieSerializer.Meta):
        fields = RecepieSerializer.Meta.fields + ['description']
