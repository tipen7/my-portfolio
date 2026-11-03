from django.utils.html import strip_tags
from rest_framework import serializers

from .models import Projects


class ProjectSerializer(serializers.ModelSerializer):
    tech_stack = serializers.ListField(
        child=serializers.CharField(allow_blank=True, max_length=50),
        required=False,
    )
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    starred_by_names = serializers.SerializerMethodField()

    class Meta:
        model = Projects
        fields = [
            "id", "name", "description",
            "type", "type_display", "url", "image", "tech_stack",
            "star_count", "is_starred", "starred_by_names",
        ]
        read_only_fields = ["id"]

    def validate_name(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Project name is required.")
        return value

    def validate_description(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Project description is required.")
        return value

    def validate_tech_stack(self, value):
        cleaned = (strip_tags(item).strip() for item in value)
        return [item for item in cleaned if item]

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return any(user.pk == request.user.pk for user in obj.starred_by.all())

    def get_starred_by_names(self, obj):
        return ", ".join(user.username for user in obj.starred_by.all())
