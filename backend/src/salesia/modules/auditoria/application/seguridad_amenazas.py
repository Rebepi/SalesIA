from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def get_threat_model(current_user: AuthenticatedUser):
    return {
        "model_version": "2026-F13",
        "system": "SalesIA Enterprise",
        "threats": [
            {
                "threat_id": "THREAT-001",
                "name": "Acceso cruzado entre empresas (BOLA / IDOR)",
                "actor": "Usuario autenticado malicioso o atacante externo",
                "boundary": "Aislamiento multi-inquilino de datos y recursos",
                "surface": "Rutas de API REST, identificadores UUID, jobs asíncronos",
                "controls": [
                    "Filtros por company_id en todas las consultas",
                    "Row Level Security en PostgreSQL",
                    "Validación estricta de contexto de sesión",
                ],
                "test": "test_sec002_object_authorization_idor",
                "responsible": "Platform Security Team",
            },
            {
                "threat_id": "THREAT-002",
                "name": "Fraude comercial y evasión de límites (Smurfing)",
                "actor": "Operador comercial o cajero coludido",
                "boundary": "Políticas de crédito, descuentos y aprobación de pedidos",
                "surface": "Creación fraccionada de ventas, notas de crédito, sobregiro",
                "controls": [
                    "Detección de fraccionamiento en ventana temporal",
                    "Prohibición de autoaprobación",
                    "Límites acumulados por cliente",
                ],
                "test": "test_sec024_business_fraud_smurfing",
                "responsible": "Financial Integrity Team",
            },
            {
                "threat_id": "THREAT-003",
                "name": "Extracción y filtración de datos sensibles (Exfiltration)",
                "actor": "Atacante interno o credenciales comprometidas",
                "boundary": "Base de datos y almacén de objetos confidenciales",
                "surface": "Exportaciones masivas, endpoints de reportería, respaldos",
                "controls": [
                    "Cadena criptográfica inmutable en auditoría",
                    "Anonimización y enmascaramiento PII",
                    "Retención legal obligatoria",
                    "Sellos SHA-256",
                ],
                "test": "test_sec011_017_data_protection",
                "responsible": "Data Protection Officer",
            },
            {
                "threat_id": "THREAT-004",
                "name": "Denegación de servicio y agotamiento de recursos (DoS)",
                "actor": "Botnet o script automatizado externo",
                "boundary": "Ingreso HTTP y capa de cómputo del servidor de aplicaciones",
                "surface": "Rutas públicas de login, subidas de archivos, consultas profundas",
                "controls": [
                    "Límites de tamaño de cuerpo 10MB/256KB",
                    "Rate limits 429 con Retry-After",
                    "Tiempos de espera estrictos",
                    "Restricciones de memoria",
                ],
                "test": "test_sec014_015_resource_protection",
                "responsible": "SRE & Infrastructure Security",
            },
        ],
        "compliance_status": "APPROVED",
    }
