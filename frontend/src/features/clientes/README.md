# Interfaz de Clientes

La carpeta `clientes` reúne el listado, el editor reutilizable, la ficha comercial y la analítica de clientes.

| Carpeta | Responsabilidad |
| --- | --- |
| `api` | Solicitudes del listado, exportación, editor, ficha y analítica. |
| `types` | Contratos de datos y propiedades de los componentes del módulo. |
| `hooks` | Carga, búsqueda, cancelación, paginación, borradores, validaciones y coordinación de acciones. |
| `pages` | Composición del listado de Clientes. |
| `components` | Estilos del listado extraídos sin cambios de los estilos anteriores. |
| `editor` | Contenedor del editor y secciones de identidad, contacto y condiciones comerciales. |
| `ficha` | Contenedor de la ficha y sus siete pestañas independientes. |
| `analitica` | Presentación de indicadores, segmentos, cohortes y tablas. |
| `utils` | Traducción de errores conservada desde el listado anterior. |

## Integraciones

`OperationsWorkspace` conserva la navegación general y la apertura de operaciones de otros módulos. Delega el listado en `ClientesPage` y su carga en `useListadoClientes`.

Ventas, Pedidos y Cotizaciones importan el mismo `CustomerEditorDrawer` desde este módulo. Se conservan sus propiedades públicas, los callbacks de guardado, el evento de actualización de entidades, los datos del borrador y su aislamiento por empresa y usuario.

El índice compartido de componentes conserva la exportación del editor para mantener compatibles los consumidores existentes. Las piezas de Clientes importan los componentes genéricos directamente, sin pasar por ese índice.

## Diseño y comportamiento

Las secciones extraídas conservan el marcado, clases, textos, identificadores y atributos accesibles anteriores. Continúan usando `ModalSurface`, `CustomSelect`, la confirmación compartida, las preferencias de paginación y los estilos globales. No se añadió una envoltura HTML alrededor de cada sección extraída.

Los nuevos archivos están dentro de las rutas que Tailwind ya inspecciona. Los archivos CSS y la configuración del tema no se modificaron.

Las pruebas `clientes-paridad.checks.tsx` contrastan 47 estados con referencias capturadas de las fuentes anteriores a la reorganización. Normalizan únicamente identificadores generados por React y espacios entre etiquetas. Es una comprobación de estructura y clases, no una comparación de píxeles en un navegador.

`clientes-flujos.checks.tsx` comprueba la integración del listado con la aplicación, la edición, selección de duplicados, recuperación de borradores, contactos, crédito, repetición de ventas, fusión, cancelación de búsquedas y corrección de página.
