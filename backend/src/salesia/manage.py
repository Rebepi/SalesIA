import argparse
import getpass
import json
import smtplib
import ssl
import time
from email.utils import formataddr
from urllib.parse import urlsplit
import psycopg2
from psycopg2 import sql
from email.message import EmailMessage
from sqlalchemy import select
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.models import CompanyModel, UserModel, BranchModel, WarehouseModel
from salesia.modules.seguridad.infrastructure.models import AuthMail
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.modules.seguridad.infrastructure.sessions import cipher, utcnow
from salesia.modules.operaciones.jobs import process_jobs
from salesia.modules.analitica.schedule_worker import process_report_schedules
from salesia.modules.finanzas.application.acuerdos_cobranza import process_collection_agreements
from salesia.modules.operaciones.application.planificacion import process_task_recurrences
from salesia.modules.auditoria.service import reseal_audit_chains


def bootstrap(args):
    password = getpass.getpass("Contraseña del administrador (mínimo 12 caracteres): ")
    if len(password) < 12 or password != getpass.getpass("Repita la contraseña: "):
        raise SystemExit("Las contraseñas no coinciden o son demasiado cortas.")
    with sync_session_factory() as db:
        if db.scalar(select(UserModel.id).where(UserModel.email == args.email.lower())):
            raise SystemExit("La cuenta ya existe; no se ha modificado.")
        company = db.scalar(select(CompanyModel).where(CompanyModel.tax_id == args.tax_id))
        if company:
            raise SystemExit("La empresa ya existe; use una invitación de su administrador.")
        company = CompanyModel(tax_id=args.tax_id, legal_name=args.name, trade_name=args.name, base_currency=args.currency)
        db.add(company)
        db.flush()
        branch = BranchModel(company_id=company.id, code="PRINCIPAL", name="Principal", timezone=args.timezone)
        db.add(branch)
        db.flush()
        db.add(WarehouseModel(company_id=company.id, branch_id=branch.id, code="PRINCIPAL", name="Principal"))
        db.add(UserModel(company_id=company.id, email=args.email.lower(), hashed_password=hash_password(password), role="company_admin", is_active=True))
        db.commit()
    print("Empresa, sucursal, almacén y administrador creados.")


def deliver_auth_mail(limit):
    if not settings.smtp_host or not settings.smtp_from:
        return 0
    sent = 0
    for _ in range(limit):
        with sync_session_factory() as db:
            mail = db.scalar(select(AuthMail).where(AuthMail.sent_at.is_(None), AuthMail.attempts < 5).order_by(AuthMail.created_at).with_for_update(skip_locked=True))
            if mail is None:
                break
            mail.attempts += 1
            message = EmailMessage()
            message["From"] = formataddr(("SalesIA Enterprise", settings.smtp_from))
            message["To"] = mail.recipient
            message["Subject"] = mail.subject
            message["Message-ID"] = f"<{mail.id}@salesia.local>"
            decrypted_body = cipher().decrypt(mail.encrypted_body.encode()).decode()
            try:
                payload = json.loads(decrypted_body)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict) and payload.get("text") and payload.get("html"):
                message.set_content(payload["text"])
                message.add_alternative(payload["html"], subtype="html")
            else:
                message.set_content(decrypted_body)
            try:
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                    if settings.smtp_starttls:
                        smtp.starttls(context=ssl.create_default_context())
                    if settings.smtp_username:
                        smtp.login(settings.smtp_username, settings.smtp_password)
                    smtp.send_message(message)
                mail.sent_at = utcnow()
                mail.encrypted_body = ""
                sent += 1
            except (OSError, smtplib.SMTPException):
                db.commit()
                raise RuntimeError("No se pudo enviar el correo; el mensaje permanece pendiente.") from None
            db.commit()
    return sent


def send_mail(args):
    if not settings.smtp_host or not settings.smtp_from:
        raise SystemExit("Configure SMTP_HOST y SMTP_FROM.")
    try:
        sent = deliver_auth_mail(args.limit)
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
    print(f"Mensajes enviados: {sent}")


def run_worker(args):
    while True:
        processed = process_jobs(args.limit)
        processed += process_report_schedules(args.limit)
        processed += process_task_recurrences(args.limit)
        processed += process_collection_agreements(args.limit)
        delivered = 0
        try:
            delivered = deliver_auth_mail(args.limit)
        except RuntimeError as error:
            print(str(error))
        if processed == 0 and delivered == 0:
            time.sleep(args.interval)


def provision_role(args):
    if not settings.app_database_password:
        raise SystemExit("Configure APP_DATABASE_PASSWORD.")
    url = settings.database_url.replace("+asyncpg", "")
    parsed = urlsplit(url)
    connection = psycopg2.connect(url)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (settings.app_database_user,))
            if cursor.fetchone():
                cursor.execute(sql.SQL("ALTER ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE").format(sql.Identifier(settings.app_database_user), sql.Literal(settings.app_database_password)))
            else:
                cursor.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE").format(sql.Identifier(settings.app_database_user), sql.Literal(settings.app_database_password)))
            cursor.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(parsed.path.lstrip("/")), sql.Identifier(settings.app_database_user)))
            cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(settings.app_database_user)))
            cursor.execute(sql.SQL("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {}").format(sql.Identifier(settings.app_database_user)))
            cursor.execute(sql.SQL("GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO {}").format(sql.Identifier(settings.app_database_user)))
            cursor.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}").format(sql.Identifier(settings.app_database_user)))
            cursor.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO {}").format(sql.Identifier(settings.app_database_user)))
    finally:
        connection.close()


def repair_audit_chain(args):
    company_id = None
    if args.company_id:
        from uuid import UUID
        company_id = UUID(args.company_id)
    with sync_session_factory() as db:
        result = reseal_audit_chains(db, company_id=company_id)
        db.commit()
    print(
        f"Cadena de auditoría reparada: {result['repaired_entries']} registros "
        f"en {result['companies']} empresas."
    )


def main():
    parser = argparse.ArgumentParser(prog="python -m salesia.manage")
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("bootstrap")
    setup.add_argument("--email", required=True)
    setup.add_argument("--tax-id", required=True)
    setup.add_argument("--name", required=True)
    setup.add_argument("--currency", default="USD", choices=["USD", "PEN", "EUR", "COP", "CLP", "MXN"])
    setup.add_argument("--timezone", default="America/Lima")
    setup.set_defaults(action=bootstrap)
    mail = commands.add_parser("send-mail")
    mail.add_argument("--limit", type=int, default=100)
    mail.set_defaults(action=send_mail)
    jobs = commands.add_parser("process-jobs")
    jobs.add_argument("--limit", type=int, default=100)
    jobs.set_defaults(action=lambda args: print(f"Trabajos procesados: {process_jobs(args.limit)}"))
    worker = commands.add_parser("worker")
    worker.add_argument("--limit", type=int, default=100)
    worker.add_argument("--interval", type=float, default=2.0)
    worker.set_defaults(action=run_worker)
    role = commands.add_parser("provision-role")
    role.set_defaults(action=provision_role)
    repair_audit = commands.add_parser("repair-audit-chain")
    repair_audit.add_argument("--company-id")
    repair_audit.set_defaults(action=repair_audit_chain)
    args = parser.parse_args()
    args.action(args)


if __name__ == "__main__":
    main()
