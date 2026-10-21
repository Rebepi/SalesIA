import hashlib as hashlib
import json as json
import os as os
import shutil as shutil
import sqlite3 as sqlite3
import subprocess as subprocess
import tempfile as tempfile
from datetime import datetime as datetime
from datetime import timedelta as timedelta
from datetime import timezone as timezone
from decimal import Decimal as Decimal
from pathlib import Path as Path
from urllib.parse import urlsplit as urlsplit
from urllib.parse import urlunsplit as urlunsplit
from uuid import UUID as UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM as AESGCM
from sqlalchemy import select as select
from sqlalchemy import update as update
from sqlalchemy.orm import Session as Session

from salesia.modules.inventario.service import move_stock as move_stock
from salesia.modules.operaciones.application.procesamiento_trabajos.cola import claim_job as claim_job
from salesia.modules.operaciones.application.procesamiento_trabajos.cola import database_backup as database_backup
from salesia.modules.operaciones.application.procesamiento_trabajos.cola import execute_backup as execute_backup
from salesia.modules.operaciones.application.procesamiento_trabajos.cola import execute_report_job as execute_report_job
from salesia.modules.operaciones.application.procesamiento_trabajos.cola import (
    mark_report_failure as mark_report_failure,
)
from salesia.modules.operaciones.application.procesamiento_trabajos.cola import now as now
from salesia.modules.operaciones.application.procesamiento_trabajos.cola import pg_dump_path as pg_dump_path
from salesia.modules.operaciones.application.procesamiento_trabajos.cola import process_jobs as process_jobs
from salesia.modules.operaciones.application.procesamiento_trabajos.cola import process_one as process_one
from salesia.modules.operaciones.application.procesamiento_trabajos.importaciones import (
    execute_import as execute_import,
)
from salesia.modules.operaciones.application.procesamiento_trabajos.importaciones import parse_decimal as parse_decimal
from salesia.modules.operaciones.import_files import read_import_file as read_import_file
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact as AnalyticsArtifact
from salesia.modules.operaciones.infrastructure_models import Notification as Notification
from salesia.modules.operaciones.infrastructure_models import UploadGrant as UploadGrant
from salesia.shared.infrastructure.config import settings as settings
from salesia.shared.infrastructure.database import sync_session_factory as sync_session_factory
from salesia.shared.infrastructure.models import AttachmentModel as AttachmentModel
from salesia.shared.infrastructure.models import BackupSnapshotModel as BackupSnapshotModel
from salesia.shared.infrastructure.models import CompanyModel as CompanyModel
from salesia.shared.infrastructure.models import CustomerModel as CustomerModel
from salesia.shared.infrastructure.models import JobModel as JobModel
from salesia.shared.infrastructure.models import ProductModel as ProductModel
from salesia.shared.infrastructure.models import UserModel as UserModel
from salesia.shared.infrastructure.models import WarehouseModel as WarehouseModel
from salesia.shared.infrastructure.tenant_scope import bind_company as bind_company
from salesia.shared.infrastructure.workers import TenantFairnessLimiter as TenantFairnessLimiter
from salesia.shared.infrastructure.workers import is_transient_error as is_transient_error
from salesia.shared.infrastructure.workers import record_dead_letter_job as record_dead_letter_job
