from django.utils.html import strip_tags
from rest_framework import serializers
from rest_framework.fields import ISO_8601

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


class ExperienceCommentSerializer(serializers.ModelSerializer):
    """Compact, read-only comment representation embedded in an experience."""

    username = serializers.CharField(source="commented_by.username", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "text", "username", "created_at"]
        read_only_fields = fields


class ExperienceSerializer(serializers.ModelSerializer):
    """
    Expects the queryset to prefetch ``starred_by`` and ``comments`` (with
    ``commented_by`` selected) so list responses do not issue per-row queries.
    """

    started_at = serializers.DateTimeField(
        input_formats=[ISO_8601, "%Y-%m-%d"], required=False,
    )
    ended_at = serializers.DateTimeField(
        input_formats=[ISO_8601, "%Y-%m-%d"], required=False, allow_null=True,
    )
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    is_ongoing = serializers.BooleanField(read_only=True)
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    starred_by_names = serializers.SerializerMethodField()
    comments = ExperienceCommentSerializer(many=True, read_only=True)
    user_comment = serializers.SerializerMethodField()

    class Meta:
        model = Experience
        fields = [
            "id", "title", "description", "category", "category_display",
            "thumbnail", "started_at", "ended_at", "is_ongoing",
            "star_count", "is_starred", "starred_by_names",
            "comments", "user_comment",
        ]
        read_only_fields = ["id"]

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

    def validate_thumbnail(self, value):
        return strip_tags(value).strip() if value else value

    def validate(self, data):
        
        started_at = data.get("started_at", getattr(self.instance, "started_at", None))
        ended_at = data.get("ended_at", getattr(self.instance, "ended_at", None))

        if started_at and ended_at and ended_at < started_at:
            raise serializers.ValidationError(
                {"ended_at": "End date must be on or after the start date."}
            )
        return data

    def get_star_count(self, obj):
        return len(obj.starred_by.all())

    def get_is_starred(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return any(user.pk == request.user.pk for user in obj.starred_by.all())

    def get_starred_by_names(self, obj):
        return ", ".join(user.username for user in obj.starred_by.all())

    def get_user_comment(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return None
        for comment in obj.comments.all():
            if comment.commented_by_id == request.user.pk:
                return {"id": str(comment.pk), "text": comment.text}
        return None


class CommentSerializer(serializers.ModelSerializer):
    """The author and the experience are never read from the request body."""

    username = serializers.CharField(source="commented_by.username", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "text", "experience", "username", "created_at", "updated_at"]
        read_only_fields = ["id", "experience", "username", "created_at", "updated_at"]

    def validate_text(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Comment text is required.")
        return value
