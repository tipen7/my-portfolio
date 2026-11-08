from django.utils.html import strip_tags
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .models import Projects, Experience, Comment


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
        return obj.starred_by.filter(pk=request.user.pk).exists()

    def get_starred_by_names(self, obj):
        return ", ".join(user.username for user in obj.starred_by.all())


class ExperienceSerializer(serializers.ModelSerializer):

    category_display = serializers.CharField(source="get_category_display", read_only=True)
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    starred_by_names = serializers.SerializerMethodField()

    class Meta:
        model = Experience
        fields = ["id", "title", "description", "category_display", "thumbnail", "started_at", "ended_at", "star_count", "is_starred", "starred_by_names", "is_ongoing"]


    def validate_title(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Experience title is required.")
        return value
    

    def validate_description(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Experience description is required.")
        return value

    def validate(self, data):
        started_at = data.get("started_at")
        ended_at = data.get("ended_at")

        if started_at and ended_at and ended_at < started_at:
            raise serializers.ValidationError("End date must be on or after the start date.")

        return data
    
    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):

        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False

        return obj.starred_by.filter(pk=request.user.pk).exists()

    def get_starred_by_names(self, obj):
        return ", ".join(user.username for user in obj.starred_by.all())

class CommentSerializer(serializers.ModelSerializer):
    
    commented_by = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Comment
        fields = ['id', 'text', 'experience', 'commented_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        validators = [
            UniqueTogetherValidator(
                queryset=Comment.objects.all(),
                fields=['experience', 'commented_by'],
                message="You have already commented on this experience."
            )
        ]


    def validate_text(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Comment text is required.")
        return value