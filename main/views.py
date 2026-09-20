from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404

from .models import Experience, Projects
from .forms import ExperienceForm, ProjectForm

# Main
def show_main(request):
    context = {
        "name": "Steven Dyanizha Ananda",
        "npm": "2506616112",
        "major": "S1 Information System",
        "bio": "I am a highly enthusiastic student who interested in Data Science and Competitive Programming."
    }

    return render(request, "index.html", context)

# Experience
def show_experience(request):
    category_query = request.GET.get("category", "").strip()
    experiences_queryset = Experience.objects.all().order_by("-started_at")

    if category_query:
        experiences_queryset = experiences_queryset.filter(category=category_query)

    experiences_json = serializers.serialize("json", experiences_queryset)
    experiences = [
        deserialized.object
        for deserialized in serializers.deserialize("json", experiences_json)
    ]

    context = {
        "name": "Steven",
        "experiences": experiences,
        "category_query": category_query,
        "experience_categories": Experience.EXPERIENCE_CHOICES,
    }

    return render(request, "experience.html", context)


def create_experience(request):
    form = ExperienceForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience created successfully.")
        return redirect("main:show_experience")

    context = {
        "name": "Steven",
        "form": form,
        "is_editing": False,
    }
    return render(request, "experience_form.html", context)


def update_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)
    form = ExperienceForm(request.POST or None, instance=experience)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience updated successfully.")
        return redirect("main:show_experience")

    context = {
        "name": "Steven",
        "form": form,
        "experience": experience,
        "is_editing": True,
    }
    return render(request, "experience_form.html", context)


def delete_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)

    if request.method == "POST":
        experience.delete()
        messages.success(request, "Experience deleted successfully.")

    return redirect("main:show_experience")


def get_experiences_json(request):
    category_query = request.GET.get("category", "").strip()
    experiences = Experience.objects.all().order_by("-started_at")

    if category_query:
        experiences = experiences.filter(category=category_query)

    experiences_json = serializers.serialize("json", experiences)
    return HttpResponse(experiences_json, content_type="application/json")

# Projects
def show_projects(request):
    title_query = request.GET.get("title", "").strip()
    projects = Projects.objects.all()

    if title_query:
        projects = projects.filter(name__icontains=title_query)

    context = {
        "name": "Burhan",
        "projects": projects,
        "title_query": title_query,
    }
    return render(request, "projects.html", context)

# Create Projects
def create_project(request):
    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project created successfully.")
        return redirect("main:show_projects")

    context = {
        "name": "Steven",
        "form": form,
    }

    return render(request, "projects_form.html", context)


def update_project(request, project_id):
    project = get_object_or_404(Projects, pk=project_id)
    form = ProjectForm(request.POST or None, instance=project)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project updated successfully.")
        return redirect("main:show_projects")

    context = {
        "name": "Steven",
        "form": form,
        "project": project,
        "is_editing": True,
    }
    return render(request, "projects_form.html", context)

def get_projects_json(request):
    title_query = request.GET.get("title", "").strip()
    projects = Projects.objects.all()

    if title_query:
        projects = projects.filter(name__icontains=title_query)

    projects_json = serializers.serialize("json", projects)
    return HttpResponse(projects_json, content_type="application/json")

# Delete Projects
def delete_project(request, project_id):
    project = get_object_or_404(Projects, pk=project_id)

    if request.method == "POST":
        project.delete()
        messages.success(request, "Project berhasil dihapus!")
        return redirect("main:show_projects")

    return redirect("main:show_projects")