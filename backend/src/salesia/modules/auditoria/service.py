import hashlib as hashlib
import json as json
import re as re
from datetime import datetime as datetime
from datetime import timedelta as timedelta
from datetime import timezone as timezone
from typing import Any as Any
from typing import Optional as Optional
from uuid import UUID as UUID
from uuid import uuid4 as uuid4

from fastapi import HTTPException as HTTPException
from fastapi import Request as Request
from fastapi import status as status
from sqlalchemy import event as event
from sqlalchemy import func as func
from sqlalchemy import select as select
from sqlalchemy import text as text
from sqlalchemy.orm import Session as Session

from salesia.modules.auditoria.application.registro.actividad import audit_privileged_access as audit_privileged_access
from salesia.modules.auditoria.application.registro.actividad import get_business_timeline as get_business_timeline
from salesia.modules.auditoria.application.registro.actividad import purge_audit_logs as purge_audit_logs
from salesia.modules.auditoria.application.registro.actividad import record_audit_event as record_audit_event
from salesia.modules.auditoria.application.registro.actividad import redact_diff as redact_diff
from salesia.modules.auditoria.application.registro.cadena import compute_chain_hash as compute_chain_hash
from salesia.modules.auditoria.application.registro.cadena import reseal_audit_chains as reseal_audit_chains
from salesia.modules.auditoria.application.registro.cadena import seal_audit_entry as seal_audit_entry
from salesia.modules.auditoria.application.registro.cadena import verify_audit_chain as verify_audit_chain
from salesia.modules.auditoria.application.registro.configuracion import CARD_PATTERN as CARD_PATTERN
from salesia.modules.auditoria.application.registro.configuracion import REDACT_KEYS as REDACT_KEYS
from salesia.modules.operaciones.infrastructure_models import LegalHold as LegalHold
from salesia.shared.infrastructure.models import AuditLogModel as AuditLogModel
