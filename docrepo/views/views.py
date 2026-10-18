from django.db import IntegrityError
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.template.context_processors import csrf
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse

from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from crispy_forms.utils import render_crispy_form

from cis.models.settings import Setting
from cis.utils import (
    user_has_cis_role, user_has_student_role,
    user_has_highschool_admin_role,
    user_has_instructor_role,
    user_has_faculty_role
)

from cis.menu import (
    cis_menu, draw_menu, STUDENT_MENU, HS_ADMIN_MENU, INSTRUCTOR_MENU, FACULTY_MENU
)

from ..models.model import DocRepo
from ..forms.docrepo import DocRepoForm

from ..serializers import DocRepoSerializer

class DocRepoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DocRepoSerializer

    def get_queryset(self):
        from datetime import datetime

        queryset = DocRepo.objects.all()
        return queryset


@user_passes_test(user_has_faculty_role, login_url='/')
def show_links_for_faculty(request):
    from ..faculty_portal import faculty_portal_setting
    portal_lang = faculty_portal_setting()
    
    menu = draw_menu(FACULTY_MENU, 'docrepo', '', 'faculty')
    template = 'docrepo/student/index.html'

    records = get_documents(request, 'faculty')

    return render(
        request,
        template, {
            'page_title': 'Documents',
            'menu': menu,
            'nav': '<nav aria-label="breadcrumb"><ol class="breadcrumb"><li class="breadcrumb-item"><a href="/">Home</a></li><li class="breadcrumb-item active" aria-current="page">Shared Docs.</li></ol></nav>',
            'intro': portal_lang(request).from_db().get('docrepo_blurb', 'Change me'),
            'records': records
            }
        )

@user_passes_test(user_has_instructor_role, login_url='/')
def show_links_for_instructor(request):
    from cis.settings.instructor_portal import instructor_portal as portal_lang
    
    menu = draw_menu(INSTRUCTOR_MENU, 'docrepo', '', 'instructor')
    template = 'docrepo/student/index.html'

    records = get_documents(request, 'instructor')

    return render(
        request,
        template, {
            'page_title': 'Documents',
            'menu': menu,
            'nav': '<nav aria-label="breadcrumb"><ol class="breadcrumb"><li class="breadcrumb-item"><a href="/instructor">Home</a></li><li class="breadcrumb-item active" aria-current="page">Shared Docs.</li></ol></nav>',
            'intro': portal_lang(request).from_db().get('docrepo_blurb', 'Change me'),
            'records': records
            }
        )

@user_passes_test(user_has_highschool_admin_role, login_url='/')
def show_links_for_highschool_admin(request):
    menu = draw_menu(HS_ADMIN_MENU, 'docrepo', '', 'highschool_admin')
    template = 'docrepo/student/index.html'

    records = get_documents(request, 'High School Administrators')

    return render(
        request,
        template, {
            'page_title': 'Documents',
            'menu': menu,
            'records': records
            }
        )

@user_passes_test(user_has_student_role, login_url='/')
def show_links_for_student(request):
    menu = draw_menu(STUDENT_MENU, 'docrepo', '', 'student')
    template = 'docrepo/student/index.html'

    records = get_documents(request, 'student')

    return render(
        request,
        template, {
            'page_title': 'Documents',
            'menu': menu,
            'records': records
            }
        )

def get_documents(request, user_role='student'):
    if user_role == 'student':
        available_to = 'Students'
    elif user_role == 'highschool_admin':
        available_to = 'High School Administrators'
    elif user_role == 'instructor':
        available_to = 'Instructors'
    elif user_role == 'faculty':
        available_to = 'Faculty'

    records = DocRepo.objects.filter(
        available_to__contains=available_to
    ).order_by('display_weight')

    return records

@user_passes_test(user_has_cis_role, login_url='/')
def delete(request, record_id):
    record = get_object_or_404(DocRepo, pk=record_id)

    try:
        record.delete()
    except Exception as e:
        messages.add_message(
            request,
            messages.SUCCESS,
            'Unable to delete record.',
            'list-group-item-danger')
        return redirect("docrepo:doc", record.id)

    messages.add_message(
        request,
        messages.SUCCESS,
        'Successfully deleted record',
        'list-group-item-success')
    return redirect("docrepo:all")

from django.views.decorators.clickjacking import xframe_options_exempt
@xframe_options_exempt
@user_passes_test(user_has_cis_role, login_url='/')
def detail(request, record_id):
    '''
    Record details page
    '''
    template = 'docrepo/details.html'
    record = get_object_or_404(DocRepo, pk=record_id)

    if request.method == 'POST':
        form = DocRepoForm(request.POST, instance=record)

        if form.is_valid():
            form.save(commit=True)
            messages.add_message(
                request,
                messages.SUCCESS,
                'Successfully updated record',
                'list-group-item-success')
            return redirect('docrepo:doc', record_id=record_id)
    else:
        form = DocRepoForm(instance=record)

    return render(
        request,
        template, {
            'form': form,
            'page_title': "Document",
            'labels': {
                'all_items': 'All Documents'
            },
            'urls': {
                'all_items': 'docrepo:all'
            },
            'menu': draw_menu(cis_menu, 'docrepo', 'all'),
            'record': record
        })

@user_passes_test(user_has_cis_role, login_url='/')
def index(request):
    '''
     search and index page for staff
    '''
    menu = draw_menu(cis_menu, 'docrepo', 'all')
    template = 'docrepo/index.html'
    
    return render(
        request,
        template, {
            'page_title': 'Documents',
            'urls': {
                'details_prefix': 'announcement/',
                'add_new': 'docrepo:all'
            },
            'menu': menu,
            'add_new_form': DocRepoForm
            }
        )

@user_passes_test(user_has_cis_role, login_url='/')
def add_new(request):
    """
    Add new for CE Staff
    """
    ajax = request.GET.get('ajax', None)
    
    if request.method == 'POST':
        """
        Add New
        """
        form = DocRepoForm(request.POST, request.FILES)

        if form.is_valid():
            record = form.save(commit=False)
            record.uploaded_by = request.user
            record.save()

            messages.add_message(
                request,
                messages.SUCCESS,
                'Successfully added record',
                'list-group-item-success'
            )
            return redirect('docrepo:doc', record_id=record.id)
    else:
        form = DocRepoForm()

    return render(
        request,
        'docrepo/add_new.html',
        {
            'base_template':'cis/logged-base.html',
            'form': form,
            'urls': {
                'all_items': 'docrepo:all'
            },
            'labels': {
                'all_items': 'All Documents'
            },
            'page_title': 'Add New Document'
        }
    )