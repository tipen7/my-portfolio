from django import forms
from django.forms import ModelForm, TextInput, Textarea, URLInput, Select
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from main.models import Experience, Projects


class ExperienceForm(ModelForm):
    started_at = forms.DateTimeField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"class": "form-control", "type": "date"},
        ),
        label=_("Start Date"),
    )
    ended_at = forms.DateTimeField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"class": "form-control", "type": "date"},
        ),
        label=_("End Date"),
    )

    class Meta:
        model = Experience
        fields = ["title", "description", "category", "thumbnail", "started_at", "ended_at"]
        labels = {
            "title": _("Experience Title"),
            "description": _("Description"),
            "category": _("Category"),
            "thumbnail": _("Thumbnail URL"),
            "started_at": _("Start Date"),
            "ended_at": _("End Date"),
        }
        widgets = {
            "title": TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Teaching Assistant, Backend Intern, ...",
                    "required": True,
                    "maxlength": 255,
                }
            ),
            "description": Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Describe your role and impact.",
                    "required": True,
                    "rows": 5,
                }
            ),
            "category": Select(
                choices=Experience.EXPERIENCE_CHOICES,
                attrs={"class": "form-control", "required": True},
            ),
            "thumbnail": URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://example.com/experience.jpg",
                    "required": False,
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        started_at = cleaned_data.get("started_at")
        ended_at = cleaned_data.get("ended_at")

        if not started_at:
            started_at = self.instance.started_at or timezone.now()
            cleaned_data["started_at"] = started_at

        if started_at and ended_at and ended_at < started_at:
            self.add_error(
                "ended_at",
                _("End date must be on or after the start date."),
            )

        return cleaned_data

class ProjectForm(ModelForm):

    tech_stack = forms.CharField(
        required=False,
        widget=TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Django, Next.js, Python (comma separated)",
            }
        ),
        label=_("Project Tech Stack"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            tech_stack = self.instance.tech_stack or []
            self.initial["tech_stack"] = ", ".join(tech_stack)

    class Meta:

        model = Projects
        exclude = ['id']

        labels = {
            "name" : _("Project Name"),
            "description" : _("Project Description"),
            "type": _("Project Type"),
            "url": _("Project Deployment URL"),
            "image": _("Project Thumbnail Image Path"),
            "tech_stack": _("Project Tech Stack"),
        }

        widgets = {
            "name": TextInput(attrs={"class": "form-control", "placeholder": "TitikTemu AI WebGIS ", "required": True, "maxlength": 50}),
            "description": Textarea(attrs={"class": "form-control", "placeholder": "TitikTemu AI WebGIS is a web-based Geographic Information System (GIS) platform...", "required": True, "maxlength": 255, "rows": 3}),
            "type": Select(choices=Projects.PROJECT_TYPE, attrs={"class": "form-control", "required": True}),
            "url": URLInput(attrs={"class": "form-control", "placeholder": "https://example.com/project", "required": False}),
            "image": URLInput(attrs={"class": "form-control", "placeholder": "https://drive.google.com/thumbnail.jpg", "required": True}),
            "tech_stack": TextInput(attrs={"class": "form-control", "placeholder": "Django, Next.js, Python (comma separated)", "required": False}),
        }



        error_messages = {
            "name": {
                "max_length": _("Project name cannot exceed 50 characters."),
            },
            "description": {
                "max_length": _("Project description cannot exceed 255 characters."),
            },
            "type": {
                "invalid_choice": _("Select a valid project type."),
            },
            "url": {
                "invalid": _("Enter a valid URL."),
            },
        }

    def clean_tech_stack(self):

        data = self.cleaned_data.get('tech_stack')

        if isinstance(data, str) and data.strip():
            return [item.strip() for item in data.split(',') if item.strip()]
        
        return data


