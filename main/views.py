from django.shortcuts import render
from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404

from .models import Experience, Projects
from .forms import ProjectForm

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
    context = {
        "name": "Steven",
        "experiences": Experience.objects.all()
    }

    return render(request, "experience.html", context)

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