from django.db.models import Q
from .models import dentistProfile, Skill, Tag, Project


def get_search_query(request):
    """Helper to extract search query from GET request."""
    return request.GET.get('search_query', '')


def searchProfiles(request):
    """
    Searches dentist profiles by:
    - first/last name
    - bio
    - skills they have
    - projects they own (by project name, description or tags)
    Returns matching profiles and their associated projects.
    """
    search_query = get_search_query(request)

    skills = Skill.objects.filter(name__icontains=search_query)
    tags = Tag.objects.filter(name__icontains=search_query)

    projects_matched = Project.objects.distinct().filter(
        Q(name__icontains=search_query) |
        Q(description__icontains=search_query) |
        Q(tags__in=tags)
    )

    profiles = dentistProfile.objects.distinct().filter(
        Q(user__first_name__icontains=search_query) |
        Q(user__last_name__icontains=search_query) |
        Q(bio__icontains=search_query) |
        Q(skill__in=skills) |
        Q(project__in=projects_matched)
    )

    # get all projects belonging to the matched profiles
    projects = Project.objects.filter(owner__in=profiles).distinct()

    return projects, profiles, search_query


def searchSkills(request):
    """
    Searches skills by:
    - skill name or description
    - owner's first/last name
    - tags
    Returns matching skills only — no profiles needed on the skills page.
    """
    search_query = get_search_query(request)

    tags = Tag.objects.filter(name__icontains=search_query)

    skills = Skill.objects.distinct().filter(
        Q(name__icontains=search_query) |
        Q(description__icontains=search_query) |
        Q(owner__user__first_name__icontains=search_query) |
        Q(owner__user__last_name__icontains=search_query) |
        Q(tags__in=tags)
    )

    return skills, search_query


def searchProjects(request):
    """
    Searches projects by:
    - project name or description
    - owner's first/last name
    - tags
    Returns matching projects and the profiles that own them.
    """
    search_query = get_search_query(request)

    tags = Tag.objects.filter(name__icontains=search_query)

    projects = Project.objects.distinct().filter(
        Q(name__icontains=search_query) |
        Q(description__icontains=search_query) |
        Q(owner__user__first_name__icontains=search_query) |
        Q(owner__user__last_name__icontains=search_query) |
        Q(tags__in=tags)
    )

    profiles = dentistProfile.objects.filter(project__in=projects).distinct()

    return projects, profiles, search_query