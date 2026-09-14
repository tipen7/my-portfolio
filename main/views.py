from django.shortcuts import render
from .models import Experience, Projects

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
    context = {
        "header": "Steven's Projects",
        "subheader": "Below listed all the successful and deployed projects",
        "projects": Projects.objects.all()
    }

    return render(request, "projects.html", context)

