from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core import serializers
from django.http import HttpResponse
from django.db.models import Prefetch
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
import datetime

from .models import Comment, Experience, Projects
from .forms import CommentForm, ExperienceForm, ProjectForm


def _is_editor_or_owner(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Editor").exists()
    )


def _require_owner(user):
    if not user.is_superuser:
        raise PermissionDenied("Access denied. This feature is only for superuser.")


def _require_editor_or_owner(user):
    if not _is_editor_or_owner(user):
        raise PermissionDenied("Access denied. You do not have the permission to access the feature.")

# Register
def register(request):

    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Account created succesfully. Please login.")
        return redirect("main:login")

    context = {
            "name": "Steven Dyanizha Ananda",
            "npm": "2506616112",
            "major": "S1 Information System",
            "bio": "I am a highly enthusiastic student who interested in Data Science and Competitive Programming.",
            "form": form,
        }

    return render(request, "register.html", context)

# Login
def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        response = redirect("main:show_main")
        response.set_cookie('last_login', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return response

    context = {
        "name": "Burhan",
        "form": form,
    }
    return render(request, "login.html", context)

# Logout
def logout_user(request):

    logout(request)
    return redirect("main:show_main")


# Main
def show_main(request):

    last_login = request.COOKIES.get('last_login', "There are login session / cookies not found")
    context = {
        "name": "Steven Dyanizha Ananda",
        "npm": "2506616112",
        "major": "S1 Information System",
        "bio": "I am a highly enthusiastic student who interested in Data Science and Competitive Programming.",
        "last_login": last_login,
    }

    return render(request, "index.html", context)

# Experience
def show_experience(request):
    category_query = request.GET.get("category", "").strip()
    experiences_queryset = Experience.objects.prefetch_related(
        Prefetch(
            "comments",
            queryset=Comment.objects.select_related("commented_by").order_by("-created_at"),
        )
    ).order_by("-started_at")

    if category_query:
        experiences_queryset = experiences_queryset.filter(category=category_query)

    experiences = list(experiences_queryset)
    for experience in experiences:
        experience.user_comment = next(
            (
                comment
                for comment in experience.comments.all()
                if request.user.is_authenticated
                and comment.commented_by_id == request.user.id
            ),
            None,
        )

    context = {
        "name": "Steven",
        "experiences": experiences,
        "category_query": category_query,
        "experience_categories": Experience.EXPERIENCE_CHOICES,
        "can_edit": _is_editor_or_owner(request.user),
        "can_manage": request.user.is_authenticated and request.user.is_superuser,
    }

    return render(request, "experience.html", context)


@login_required(login_url="/login/")
@require_POST
def comment_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)
    comment = Comment.objects.filter(
        experience=experience,
        commented_by=request.user,
    ).first()
    form = CommentForm(request.POST, instance=comment)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.experience = experience
        comment.commented_by = request.user
        comment.save()
        messages.success(request, "Comment saved successfully.")
    else:
        messages.error(request, "Please enter a comment of 100 characters or fewer.")

    return redirect("main:show_experience")


@login_required(login_url="/login/")
def create_experience(request):
    _require_owner(request.user)
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

@login_required(login_url="/login/")
def update_experience(request, experience_id):
    _require_editor_or_owner(request.user)
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


@login_required(login_url="/login/")
@require_POST
def delete_experience(request, experience_id):
    _require_owner(request.user)
    experience = get_object_or_404(Experience, pk=experience_id)

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
        "can_edit": _is_editor_or_owner(request.user),
        "can_manage": request.user.is_authenticated and request.user.is_superuser,
    }
    return render(request, "projects.html", context)

# Create Projects
@login_required(login_url="/login/")
def create_project(request):
    _require_owner(request.user)

    
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

@login_required(login_url="/login/")
def update_project(request, project_id):
    _require_editor_or_owner(request.user)
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

    projects_json = serializers.serialize(
        "json",
        projects,
        fields=["name", "description", "type", "url", "image", "tech_stack"],
        use_natural_foreign_keys=True,
    )
    return HttpResponse(projects_json, content_type="application/json") 

# Delete Projects
@login_required(login_url="/login/")
@require_POST
def delete_project(request, project_id):
    _require_owner(request.user)
    project = get_object_or_404(Projects, pk=project_id)

    project.delete()
    messages.success(request, "Project berhasil dihapus!")
    return redirect("main:show_projects")


@login_required(login_url="/login/")
@require_POST
def toggle_star(request, project_id):
    project = get_object_or_404(Projects, pk=project_id)

    if project.starred_by.filter(pk=request.user.pk).exists():
        project.starred_by.remove(request.user)
    else:
        project.starred_by.add(request.user)

    return redirect("main:show_projects")