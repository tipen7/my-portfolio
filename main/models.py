import uuid
from django.db import models

class Experience(models.Model):

    EXPERIENCE_CHOICES = [
        ("internship", "Internship"),
        ("volunteer", "Volunteer"),
        ("part-time", "Part-Time"),
        ("full-time", "Full-Time"),
        ("freelance", "Freelance"),
        ("research", "Research")
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(choices=EXPERIENCE_CHOICES, max_length=20, default="freelance")
    thumbnail = models.URLField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

    @property
    def is_ongoing(self):
        return self.ended_at is None

class Projects(models.Model):

    PROJECT_TYPE = [
        ("personal", "Personal"),
        ("competition", "Competition"),
        ("team", "Team")
    ]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False) # Primary key
    name = models.CharField(max_length=50) # Project name is limited to 50 characters
    description = models.TextField(max_length=255) # Project's description
    type = models.CharField(choices=PROJECT_TYPE, max_length=15, default="personal") # Project Enum type
    url = models.URLField(max_length=255, blank=True, null=True) # Project deployment URL
    image = models.CharField(max_length=255) # Image path in the directory for thumbnail purpose
    tech_stack = models.JSONField(default=list, blank=True) # Project tech stack (display purpose)
    