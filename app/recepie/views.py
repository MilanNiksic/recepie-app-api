from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import (
    viewsets,
    mixins,
    status,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Recepie,
    Tag,
    Ingridient,
)
from recepie import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='CSV of IDs to filter'
            ),
            OpenApiParameter(
                'ingridients',
                OpenApiTypes.STR,
                description='CSV of IDs to filter'
            ),
        ]
    )
)
class RecepieViewSet(viewsets.ModelViewSet):

    serializer_class = serializers.RecepieDetailSerializer
    queryset = Recepie.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        tags = self.request.query_params.get('tags')
        ingridients = self.request.query_params.get('ingridients')
        queryset = self.queryset
        if tags:
            tags_id = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tags_id)
        if ingridients:
            ingridients_id = self._params_to_ints(ingridients)
            queryset = queryset.filter(ingridients__id__in=ingridients_id)

        return queryset.filter(
            user=self.request.user
        ).order_by('-id').distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.RecepieSerializer
        if self.action == 'upload_image':
            return serializers.RecepieImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to recipes.'
            )
        ]
    )
)
class BaseRecepieAttrViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recepie__isnull=False)

        return queryset.filter(
            user=self.request.user
        ).order_by('-name').distinct()


class TagViewSet(BaseRecepieAttrViewSet):

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngridientViewSet(BaseRecepieAttrViewSet):

    serializer_class = serializers.IngridientSerializer
    queryset = Ingridient.objects.all()
