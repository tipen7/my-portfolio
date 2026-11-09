from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes,
)
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from django.db.models import Prefetch

from main.models import Comment, Experience, Projects
from main.permissions import IsPortfolioOwnerOrEditorOrReadOnly
from main.serializers import CommentSerializer, ExperienceSerializer, ProjectSerializer


def _projects_queryset():
    return Projects.objects.prefetch_related("starred_by").order_by("name", "id")


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def project_list(request):
    if request.method in ("GET", "HEAD"):
        projects = _projects_queryset()
        name = request.query_params.get("name", "").strip()
        project_type = request.query_params.get("type", "").strip()
        if name:
            projects = projects.filter(name__icontains=name)
        if project_type:
            projects = projects.filter(type=project_type)

        serializer = ProjectSerializer(projects, many=True, context={"request": request})
        return Response(serializer.data)

    serializer = ProjectSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def project_detail(request, project_id):
    project = get_object_or_404(_projects_queryset(), pk=project_id)
    if request.method in ("GET", "HEAD"):
        serializer = ProjectSerializer(project, context={"request": request})
        return Response(serializer.data)

    if request.method == "DELETE":
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ProjectSerializer(
        project, data=request.data, partial=request.method == "PATCH",
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def project_star(request, project_id):
    project = get_object_or_404(Projects, pk=project_id)
    if project.starred_by.filter(pk=request.user.pk).exists():
        project.starred_by.remove(request.user)
    else:
        project.starred_by.add(request.user)
    project = _projects_queryset().get(pk=project.pk)
    serializer = ProjectSerializer(project, context={"request": request})
    return Response(serializer.data)


# ======== EXPERIENCE ======== #
def _experiences_queryset():
    return Experience.objects.prefetch_related(
        "starred_by",
        Prefetch(
            "comments",
            queryset=Comment.objects.select_related("commented_by").order_by("-created_at"),
        ),
    ).order_by("-started_at", "title", "id")


def _serialize_experience(experience, request):
    
    experience = _experiences_queryset().get(pk=experience.pk)
    return ExperienceSerializer(experience, context={"request": request}).data


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def experience_list(request):
    if request.method in ("GET", "HEAD"):
        experiences = _experiences_queryset()
        search = request.query_params.get("search", "").strip()
        category = request.query_params.get("category", "").strip()
        if search:
            experiences = experiences.filter(title__icontains=search)
        if category:
            experiences = experiences.filter(category=category)

        serializer = ExperienceSerializer(experiences, many=True, context={"request": request})
        return Response(serializer.data)

    serializer = ExperienceSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    experience = serializer.save()
    return Response(_serialize_experience(experience, request), status=status.HTTP_201_CREATED)


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def experience_detail(request, experience_id):
    experience = get_object_or_404(_experiences_queryset(), pk=experience_id)

    if request.method in ("GET", "HEAD"):
        serializer = ExperienceSerializer(experience, context={"request": request})
        return Response(serializer.data)

    if request.method == "DELETE":
        experience.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ExperienceSerializer(
        experience, data=request.data, partial=request.method == "PATCH",
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    experience = serializer.save()
    return Response(_serialize_experience(experience, request))


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def experience_star(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)
    
    if experience.starred_by.filter(pk=request.user.pk).exists():
        experience.starred_by.remove(request.user)
    else:
        experience.starred_by.add(request.user)
    return Response(_serialize_experience(experience, request))


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticatedOrReadOnly])
def experience_comment_list(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)

    if request.method in ("GET", "HEAD"):
        comments = experience.comments.select_related("commented_by").order_by("-created_at")
        serializer = CommentSerializer(comments, many=True, context={"request": request})
        return Response(serializer.data)

    existing = Comment.objects.filter(experience=experience, commented_by=request.user).first()
    serializer = CommentSerializer(existing, data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save(experience=experience, commented_by=request.user)
    return Response(
        serializer.data,
        status=status.HTTP_200_OK if existing else status.HTTP_201_CREATED,
    )
