from salesia.modules.auditoria.application.contracts.privacidad_mask_data import MaskDataRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def mask_personal_data(payload: MaskDataRequest, current_user: AuthenticatedUser):
    masked = {}
    for k, v in payload.data.items():
        if not v:
            masked[k] = ""
            continue
        if "@" in v:
            parts = v.split("@")
            masked[k] = f"{parts[0][:1]}***@{parts[1]}"
        elif len(v) >= 8:
            masked[k] = f"{v[:2]}***{v[-2:]}"
        elif len(v) >= 4:
            masked[k] = f"{v[:1]}***{v[-1:]}"
        else:
            masked[k] = "***"
    return {"masked_data": masked}
