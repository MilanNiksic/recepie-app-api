from rest_framework import serializers
from core.models import (
    Recepie,
    Tag,
    Ingridient,
)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class IngridientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingridient
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecepieSerializer(serializers.ModelSerializer):

    tags = TagSerializer(many=True, required=False)
    ingridients = IngridientSerializer(many=True, required=False)

    class Meta:
        model = Recepie
        fields = [
            'id', 'title', 'time_minutes', 'price', 'link', 'tags',
            'ingridients',
        ]
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, recepie):
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag
            )
            recepie.tags.add(tag_obj)

    def _get_or_create_ingridients(self, ingridients, recepie):
        auth_user = self.context['request'].user
        for ingridient in ingridients:
            ingridient_obj, created = Ingridient.objects.get_or_create(
                user=auth_user,
                **ingridient
            )
            recepie.ingridients.add(ingridient_obj)

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        ingridients = validated_data.pop('ingridients', [])
        recepie = Recepie.objects.create(**validated_data)
        self._get_or_create_tags(tags, recepie)
        self._get_or_create_ingridients(ingridients, recepie)

        return recepie

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingridients = validated_data.pop('ingridients', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        if ingridients is not None:
            instance.ingridients.clear()
            self._get_or_create_ingridients(ingridients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RecepieDetailSerializer(RecepieSerializer):

    class Meta(RecepieSerializer.Meta):
        fields = RecepieSerializer.Meta.fields + ['description']
