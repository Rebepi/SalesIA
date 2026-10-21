# Módulo Clientes

Este módulo conserva las rutas públicas `/customers`, `/crm` y `/customer-portal`. El nombre de la carpeta interna es `clientes`; los permisos, eventos, nombres de tablas y contratos externos mantienen sus identificadores existentes.

## Distribución

| Carpeta | Responsabilidad |
| --- | --- |
| `presentation/routes` | Adaptadores HTTP organizados por operación; conservan parámetros, dependencias, respuestas y códigos de estado. |
| `presentation/router.py` | Composición de los tres routers públicos y conservación explícita del orden de registro anterior. |
| `presentation/dependencies.py` | Resolución del cliente autorizado en el portal. |
| `application/contracts` | Contratos Pydantic de creación, edición, CRM, archivos y fidelización. |
| `application` | Casos de uso, consultas y operaciones transaccionales, agrupados por responsabilidad. |
| `domain` | Normalización de texto y similitud de nombres sin acceso a la base de datos. |
| `infrastructure/models.py` | Modelo principal del cliente y sus nueve modelos complementarios. |
| `infrastructure/perfiles.py` | Obtención y creación del perfil comercial dentro de la sesión existente. |

Los casos de uso están separados en consulta, creación, edición, estados, duplicados, fusión, contactos, direcciones, estado de cuenta, historial, condiciones, asignaciones, segmentos, notas, importación, exportación, calidad, oportunidades, actividades, fidelización y portal.

## Compatibilidad

`salesia.shared.infrastructure.models` conserva la exportación del mismo objeto `CustomerModel` para los módulos todavía no reorganizados. El modelo se define una sola vez dentro de Clientes. No se cambia el esquema SQL ni se requiere una migración por esta reorganización.

La política central de autorización reconoce el nombre interno `clientes` y exige los mismos permisos `customers:*` utilizados antes. Las rutas continúan aplicando sus dependencias específicas y el portal mantiene su resolución de identidad.

Las operaciones conservan sus límites transaccionales: mover una función de archivo no añade confirmaciones de transacción ni divide una escritura en varios guardados independientes.

## Mantenimiento

Una ruta debe limitarse a recibir parámetros y delegar. Las reglas y la coordinación de operaciones se mantienen en los casos de uso correspondientes. Los contratos de aplicación no dependen de los routers. No se importan rutas desde dominio, aplicación o infraestructura.

No se crea un archivo por cumplir un límite arbitrario de líneas. La separación responde a responsabilidades que puedan revisarse y comprobarse por separado.

La prueba `backend/tests/test_clientes_contract.py` protege las rutas, el orden y los esquemas públicos. Los recorridos CRM, portal, permisos, aislamiento y operaciones relacionadas se verifican con las suites existentes.
