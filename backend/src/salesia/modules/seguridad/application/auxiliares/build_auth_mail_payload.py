from html import escape


def build_auth_mail_payload(user, purpose, link, company_name, invited_by=None, role_name=None):
    safe_company = escape(company_name or "SalesIA Enterprise")
    safe_email = escape(user.email)
    safe_link = escape(link, quote=True)
    safe_inviter = escape(invited_by or "el equipo administrador")
    safe_role = escape(role_name or user.role)
    is_invitation = purpose == "invitation"
    heading = "Te invitaron a SalesIA" if is_invitation else "Restablece tu contraseña"
    description = (
        f"{safe_inviter} te invitó a colaborar en {safe_company}."
        if is_invitation
        else f"Recibimos una solicitud para restablecer el acceso de {safe_email}."
    )
    action_label = "Aceptar invitación" if is_invitation else "Crear nueva contraseña"
    role_row = (
        f'<tr><td style="padding:8px 0;color:#64748b;font-size:14px">Rol asignado</td><td style="padding:8px 0;color:#0f172a;font-size:14px;font-weight:700;text-align:right">{safe_role}</td></tr>'
        if is_invitation
        else ""
    )
    text = (
        f"{heading}\n\n{description}\n"
        + (f"Rol asignado: {role_name or user.role}\n" if is_invitation else "")
        + f"\n{action_label}:\n{link}\n\nEl enlace caduca en una hora y solo puede utilizarse una vez.\nSi no esperabas este mensaje, puedes ignorarlo."
    )
    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<title>{heading}</title>
</head>
<body style="margin:0;padding:0;background:#eef3f8;font-family:Inter,Segoe UI,Arial,sans-serif;color:#0f172a">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{description} El enlace caduca en una hora.</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#eef3f8;padding:32px 12px">
<tr><td align="center">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:620px;background:#ffffff;border:1px solid #dce6ef;border-radius:24px;overflow:hidden;box-shadow:0 18px 45px rgba(15,23,42,.12)">
<tr><td style="padding:30px 36px;background:#073b4c;background:linear-gradient(135deg,#073b4c 0%,#0f766e 100%)">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr>
<td><div style="display:inline-block;width:42px;height:42px;line-height:42px;text-align:center;border-radius:13px;background:#14b8a6;color:#ffffff;font-size:22px;font-weight:800">S</div></td>
<td style="padding-left:12px;color:#ffffff"><div style="font-size:20px;font-weight:800;letter-spacing:-.3px">SalesIA</div><div style="font-size:11px;letter-spacing:1.8px;color:#99f6e4;font-weight:700">ENTERPRISE</div></td>
<td align="right" style="font-size:12px;color:#ccfbf1">Acceso seguro</td>
</tr></table>
</td></tr>
<tr><td style="padding:38px 36px 18px">
<div style="display:inline-block;padding:6px 10px;border-radius:999px;background:#ccfbf1;color:#115e59;font-size:11px;font-weight:800;letter-spacing:.7px;text-transform:uppercase">{safe_company}</div>
<h1 style="margin:18px 0 10px;font-size:28px;line-height:1.2;letter-spacing:-.6px;color:#0f172a">{heading}</h1>
<p style="margin:0;color:#475569;font-size:16px;line-height:1.65">{description}</p>
</td></tr>
<tr><td style="padding:8px 36px 24px">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:16px;padding:14px 18px">
<tr><td style="padding:8px 0;color:#64748b;font-size:14px">Cuenta</td><td style="padding:8px 0;color:#0f172a;font-size:14px;font-weight:700;text-align:right">{safe_email}</td></tr>
{role_row}
<tr><td style="padding:8px 0;color:#64748b;font-size:14px">Vigencia</td><td style="padding:8px 0;color:#0f172a;font-size:14px;font-weight:700;text-align:right">1 hora</td></tr>
</table>
</td></tr>
<tr><td align="center" style="padding:4px 36px 30px">
<a href="{safe_link}" style="display:inline-block;background:#0f766e;color:#ffffff;text-decoration:none;font-size:16px;font-weight:800;padding:15px 28px;border-radius:13px;box-shadow:0 8px 18px rgba(15,118,110,.25)">{action_label}</a>
</td></tr>
<tr><td style="padding:0 36px 34px">
<div style="border-top:1px solid #e2e8f0;padding-top:22px;color:#64748b;font-size:13px;line-height:1.6">
Este enlace es personal, caduca en una hora y solo puede utilizarse una vez. Si el botón no funciona, copia esta dirección en tu navegador:<br>
<a href="{safe_link}" style="color:#0f766e;word-break:break-all">{safe_link}</a>
</div>
</td></tr>
<tr><td style="padding:22px 36px;background:#f8fafc;color:#94a3b8;font-size:12px;line-height:1.55;text-align:center">
Mensaje automático de SalesIA Enterprise. No compartas este enlace ni respondas a este correo.
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""
    return {"text": text, "html": html}
