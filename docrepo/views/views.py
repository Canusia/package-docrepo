from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.http import (
    HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse,
)

from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response


from cis.models.settings import Setting
from cis.utils import (
    user_has_cis_role, user_has_student_role,
    user_has_highschool_admin_role,
    user_has_instructor_role,
    user_has_faculty_role,
    CIS_user_only,
)

from cis.menu import (
    cis_menu, draw_menu, STUDENT_MENU, HS_ADMIN_MENU, INSTRUCTOR_MENU, FACULTY_MENU
)

from ..models.model import DocRepo
from ..access import can_open

from ..forms.docrepo import DocRepoForm

from ..serializers import DocRepoSerializer
from ..actions import absolute_file_link, docrepo_actions

try:   # cis.menu_registry: register portal pages with the sidebar registry
    from cis.menu_registry import menu as _menu
except ImportError:   # cis without the registry
    _menu = None


def _menu_item(*args, **kwargs):
    """`menu.item` when cis has the registry, else a no-op decorator."""
    if _menu is None:
        return lambda view: view
    return _menu.item(*args, **kwargs)

class DocRepoViewSet(viewsets.ReadOnlyModelViewSet):
    """CE's document table. Every document, so CE only."""
    serializer_class = DocRepoSerializer
    permission_classes = [CIS_user_only]

    def get_queryset(self):
        from datetime import datetime

        queryset = DocRepo.objects.all()
        return queryset


@user_passes_test(user_has_faculty_role, login_url='/')
def show_links_for_faculty(request):
    from ..portal_text import portal_text
    
    menu = draw_menu(FACULTY_MENU, 'docrepo', '', 'faculty')
    template = 'docrepo/student/index.html'

    records = get_documents(request, 'faculty')

    return render(
        request,
        template, {
            'page_title': 'Documents',
            'menu': menu,
            'nav': '<nav aria-label="breadcrumb"><ol class="breadcrumb"><li class="breadcrumb-item"><a href="/">Home</a></li><li class="breadcrumb-item active" aria-current="page">Shared Docs.</li></ol></nav>',
            'intro': portal_text('faculty').get('docrepo_blurb', 'Change me'),
            'records': records
            }
        )

@user_passes_test(user_has_instructor_role, login_url='/')
def show_links_for_instructor(request):
    from ..portal_text import portal_text
    
    menu = draw_menu(INSTRUCTOR_MENU, 'docrepo', '', 'instructor')
    template = 'docrepo/student/index.html'

    records = get_documents(request, 'instructor')

    return render(
        request,
        template, {
            'page_title': 'Documents',
            'menu': menu,
            'nav': '<nav aria-label="breadcrumb"><ol class="breadcrumb"><li class="breadcrumb-item"><a href="/instructor">Home</a></li><li class="breadcrumb-item active" aria-current="page">Shared Docs.</li></ol></nav>',
            'intro': portal_text('instructor').get('docrepo_blurb', 'Change me'),
            'records': records
            }
        )

# Added hidden (default_visible=False): CE turns them on in the menu editor.
@_menu_item('highschool_admin', 'docrepo', 'Documents',
            url='highschool_admin_docrepo:docs', icon='fas fa-fw fa-folder',
            order=105, default_visible=False)
@user_passes_test(user_has_highschool_admin_role, login_url='/')
def show_links_for_highschool_admin(request):
    menu = draw_menu(HS_ADMIN_MENU, 'docrepo', '', 'highschool_admin')
    template = 'docrepo/student/index.html'

    records = get_documents(request, 'highschool_admin')

    return render(
        request,
        template, {
            'page_title': 'Documents',
            'menu': menu,
            'nav': '<nav aria-label="breadcrumb"><ol class="breadcrumb"><li class="breadcrumb-item"><a href="/highschool_admin/">Home</a></li><li class="breadcrumb-item active" aria-current="page">Documents</li></ol></nav>',
            'records': records
            }
        )

@_menu_item('student', 'docrepo', 'Documents', url='student_docrepo:docs',
            icon='fas fa-fw fa-folder', order=55, default_visible=False)
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
    from ..access import ROLE_LABELS
    available_to = ROLE_LABELS.get(user_role)
    if available_to is None:
        return DocRepo.objects.none()

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
        form = DocRepoForm(request.POST, request.FILES, instance=record)

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
            'record': record,
            'form_assets': form.media,
            'file_link': absolute_file_link(request, record),
            'shared_with_hs_admins': 'High School Administrators' in set(
                record.available_to or ()),
        })

@user_passes_test(user_has_cis_role, login_url='/')
def index(request):
    '''
     search and index page for staff
    '''
    menu = draw_menu(cis_menu, 'docrepo', 'all')
    template = 'docrepo/index.html'
    add_new_form = DocRepoForm()
    
    return render(
        request,
        template, {
            'page_title': 'Documents',
            'urls': {
                'details_prefix': 'announcement/',
                'add_new': 'docrepo:all'
            },
            'menu': menu,
            'add_new_form': add_new_form,
            'form_assets': add_new_form.media,
            'bulk_actions': docrepo_actions.for_scope('bulk', request.user),
            }
        )


@user_passes_test(user_has_cis_role, login_url='/')
def bulk_actions(request):
    """Dispatch point for the documents table's bulk actions."""
    slug = request.POST.get('action') or request.GET.get('action')
    known = {s for group in docrepo_actions.for_scope('bulk').values() for s in group['actions']}
    if slug not in known:
        # unknown action before the POST-only check, as cis's bulk endpoints do
        return JsonResponse({'status': 'error', 'message': 'Unknown action.'}, status=400)
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    return docrepo_actions.dispatch(request, slug)

@user_passes_test(user_has_cis_role, login_url='/')
def add_new(request):
    """
    Add new for CE Staff. The documents page's Add New panel posts here with
    AJAX and gets JSON back; a plain post (the standalone page) redirects to
    the new document.
    """
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = DocRepoForm(request.POST, request.FILES)

        if form.is_valid():
            record = form.save(commit=False)
            record.uploaded_by = request.user
            record.save()

            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'message': f'Added "{record.title}".',
                    'ce_url': str(record.ce_url),
                })

            messages.add_message(
                request,
                messages.SUCCESS,
                'Successfully added record',
                'list-group-item-success'
            )
            return redirect('docrepo:doc', record_id=record.id)

        if is_ajax:
            return JsonResponse({
                'message': 'Please correct the errors and try again.',
                'errors': form.errors.as_json(),
            }, status=400)
    else:
        form = DocRepoForm()

    return render(
        request,
        'docrepo/add_new.html',
        {
            'base_template':'cis/logged-base.html',
            'form': form,
            'form_assets': form.media,
            'urls': {
                'all_items': 'docrepo:all'
            },
            'labels': {
                'all_items': 'All Documents'
            },
            'page_title': 'Add New Document'
        }
    )

@login_required
def open_file(request, record_id):
    """Permanent link to a document's file (docrepo_files:open).

    The file itself is private storage, so its URL is signed and expires;
    this link never does. It checks the viewer can see the document, then
    redirects to a freshly signed URL.
    """
    record = get_object_or_404(DocRepo, pk=record_id)
    if not can_open(request.user, record):
        return HttpResponseForbidden(
            'This document is not shared with your role.')
    return redirect(record.media.url)
