from rest_framework.permissions import BasePermission, SAFE_METHODS

EDITOR_GROUP_NAME = "Editor"


def is_portfolio_owner(user):
    return bool(user and user.is_authenticated and user.is_superuser)


def is_editor(user):
    return bool(
        user
        and user.is_authenticated
        and user.groups.filter(name=EDITOR_GROUP_NAME).exists()
    )


class IsPortfolioOwnerOrReadOnly(BasePermission):
    """Anyone may read; only the portfolio owner (superuser) may write."""

    message = "Only the portfolio owner can change projects."

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_portfolio_owner(request.user)


class IsPortfolioOwnerOrEditorOrReadOnly(BasePermission):
    """
    Role-based permission for a single-owner portfolio:

    - visitor / regular user: read only (GET, HEAD, OPTIONS)
    - Editor group member: read + update (PUT, PATCH)
    - owner (superuser): everything, including create (POST) and DELETE

    This does NOT filter objects per user. If the app ever has many owners
    and private data, object-level checks and queryset scoping are needed.
    """

    message = "Only the portfolio owner or an Editor can change projects."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if is_portfolio_owner(request.user):
            return True
        return request.method in ("PUT", "PATCH") and is_editor(request.user)
