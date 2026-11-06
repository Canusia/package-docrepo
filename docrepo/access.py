"""Who may open a document: CE always; anyone else when one of their roles is
in the document's Available To."""
from cis.utils import (
    user_has_cis_role, user_has_faculty_role, user_has_highschool_admin_role,
    user_has_instructor_role, user_has_student_role,
)

#: Portal role -> the Available To label it reads.
ROLE_LABELS = {
    'student': 'Students',
    'highschool_admin': 'High School Administrators',
    'instructor': 'Instructors',
    'faculty': 'Faculty',
}

_ROLE_CHECKS = {
    'student': user_has_student_role,
    'highschool_admin': user_has_highschool_admin_role,
    'instructor': user_has_instructor_role,
    'faculty': user_has_faculty_role,
}


def can_open(user, record):
    if not user.is_authenticated:
        return False
    if user_has_cis_role(user):
        return True
    available = set(record.available_to or ())
    return any(label in available and _ROLE_CHECKS[role](user)
               for role, label in ROLE_LABELS.items())
