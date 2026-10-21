from salesia.shared.infrastructure.errors import DomainForbiddenException


def purchase_attachment_access(attachment, user, write=False):

    if attachment and attachment.related_entity_type == "purchase_order":
        permission = "purchases:write" if write else "purchases:read"

        if permission not in user.permissions:
            raise DomainForbiddenException("No tienes permiso para acceder a los adjuntos de compras.")
