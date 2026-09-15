from django import forms
from django.forms import ModelForm, TextInput, Textarea, URLInput, Select
from django.utils.translation import gettext_lazy as _

from main.models import Projects

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


