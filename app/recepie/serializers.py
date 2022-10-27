from rest_framework import serializers
from core.models import (
    Recepie,
    Tag,
)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecepieSerializer(serializers.ModelSerializer):

    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Recepie
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags']
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, recepie):
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag
            )
            recepie.tags.add(tag_obj)

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        recepie = Recepie.objects.create(**validated_data)
        self._get_or_create_tags(tags, recepie)

        return recepie

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RecepieDetailSerializer(RecepieSerializer):

    class Meta(RecepieSerializer.Meta):
        fields = RecepieSerializer.Meta.fields + ['description']
