from django.shortcuts import render
from .models import dentistProfile,Skill,Project

# Create your views here.


def profiles(request):
    profiles = dentistProfile.objects.all()
    context = {'profiles': profiles}
    return render(request, 'dentists/profiles.html',context)

def profile(request, profile_id):
    profile = dentistProfile.objects.get(id=profile_id)
    topSkills = profile.d_skill.exclude(description__exact="") # - In short, this returns all `Skill`
    # objects related
                            # to the given `profile` **except those where the description is empty**.

    otherSkills = profile.d_skill.filter(description="") # skills without admin description, shown as OTHER
    # SKILLS in template
    dentistProjects = profile.d_project.all ()
    context = {'profile': profile,'topSkills':topSkills,'otherSkills':otherSkills,'dentistProjects':dentistProjects,}

    return render(request, 'dentists/profile.html',context)

def skills(request):
    all_skills = Skill.objects.all()
    context = {'skills': all_skills}
    return render(request, 'dentists/skills.html', context)

def skill(request,skill_id):
    skillObj = Skill.objects.get(id=skill_id)
    # tags = projectObj.tags.all()
    return render(request, 'dentists/skill.html', {'skill':skillObj,})

def projects(request):
    all_projects = Project.objects.all()
    context = {'projects':all_projects}
    return render(request, 'dentists/projects.html', context)


def project(request,project_id):
    projObj = Project.objects.get(id=project_id)
    return render(request, 'dentists/project.html', {'project':projObj})



