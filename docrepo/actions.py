"""CE bulk actions for the documents table (cis ActionRegistry pattern).

copy_links: a modal with the permanent link (docrepo_files:open) of each
selected document, each with a Copy button, plus Copy all.
"""
import uuid
from collections import OrderedDict

from django.http import JsonResponse
from django.template.loader import render_to_string

from myce.component_registry import ActionRegistry

from cis.utils import user_has_cis_role

from .models.model import DocRepo

HS_ADMINS = DocRepo.SCHOOL_ADMINS

docrepo_actions = ActionRegistry(OrderedDict({
    'documents': {'actions': OrderedDict()},
}))


def absolute_file_link(request, record):
    """The document's permanent link as an absolute URL, or None when the host
    hasn't mounted docrepo_files. Never the signed media URL: that expires."""
    link = record.file_link
    return request.build_absolute_uri(link) if link else None


def _selected_ids(request):
    ids = []
    for raw in request.POST.getlist('ids[]'):
        try:
            ids.append(uuid.UUID(str(raw)))
        except ValueError:
            continue
    return ids


@docrepo_actions.action(
    'documents',
    label='Copy Links',
    scope=['bulk'],
    slug='copy_links',
    icon='fas fa-link',
    btn_class='btn-primary',
    permission=user_has_cis_role,
)
def copy_links(request):
    records = DocRepo.objects.filter(pk__in=_selected_ids(request)).order_by(
        'display_weight', 'title')
    rows = [{
        'record': record,
        'link': absolute_file_link(request, record),
        'shared_with_hs_admins': HS_ADMINS in set(record.available_to or ()),
    } for record in records]
    links_available = all(row['link'] for row in rows)
    html = render_to_string('docrepo/_copy_links_modal.html', {
        'rows': rows,
        'links_available': links_available,
        'all_links': '\n'.join(
            f"{row['record'].title}: {row['link']}" for row in rows if row['link']),
    }, request=request)
    return JsonResponse({'outcome': 'modal', 'html': html})
