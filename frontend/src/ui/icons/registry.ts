export interface IconRegistryEntry {
  id: string;
  name: string;
  componentName: string;
  originalUrl: string;
  version: string;
  license: string;
  application: string;
  adaptation: string;
  durationMs: number;
  gestureType: string;
}

export const ICON_DEPENDENCY_REGISTRY: IconRegistryEntry[] = [
  {
    id: "ICO-001",
    name: "square-pen",
    componentName: "SquarePenIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/square-pen.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Formularios, tablas y detalle; activar abre edición y nunca guarda automáticamente",
    adaptation: "Inclinar ligeramente el lápiz 10deg y dibujar un trazo corto, 240 ms, viewBox fijo 24x24",
    durationMs: 240,
    gestureType: "tilt-stroke"
  },
  {
    id: "ICO-002",
    name: "plus",
    componentName: "PlusIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/plus.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Nuevo cliente, línea de pedido, producto y nueva regla",
    adaptation: "Pequeña expansión 1.0->1.08->1.0, 180 ms",
    durationMs: 180,
    gestureType: "scale-pulse"
  },
  {
    id: "ICO-003",
    name: "check",
    componentName: "CheckIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/check.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Guardar formularios y confirmar pasos; durante envío mostrar progreso",
    adaptation: "Dibujar el check una vez, 200 ms, solo éxito tras respuesta",
    durationMs: 200,
    gestureType: "draw-check"
  },
  {
    id: "ICO-004",
    name: "x",
    componentName: "XIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/x.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Cerrar overlays; advertir si hay cambios pendientes",
    adaptation: "Cambio de color y giro mínimo 8 grados, 140 ms",
    durationMs: 140,
    gestureType: "rotate-color"
  },
  {
    id: "ICO-005",
    name: "copy",
    componentName: "CopyIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/copy.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Códigos, enlaces y referencias; comunicar fallo del portapapeles",
    adaptation: "Desplazar las hojas 1-2 px y confirmar con check, 220 ms",
    durationMs: 220,
    gestureType: "shift-sheets"
  },
  {
    id: "ICO-006",
    name: "download",
    componentName: "DownloadIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/download.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Reportes disponibles; no presentar descarga lista mientras se genera",
    adaptation: "Flecha hacia abajo 2 px y retorno, 220 ms",
    durationMs: 220,
    gestureType: "translate-y-down"
  },
  {
    id: "ICO-007",
    name: "upload",
    componentName: "UploadIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/upload.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Importaciones y adjuntos; progreso separado del gesto",
    adaptation: "Flecha ascendente 2 px y retorno, 220 ms",
    durationMs: 220,
    gestureType: "translate-y-up"
  },
  {
    id: "ICO-008",
    name: "search",
    componentName: "SearchIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/search.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Búsqueda global y listados; no disparar consulta por hover",
    adaptation: "Inclinación leve de lupa, 180 ms",
    durationMs: 180,
    gestureType: "tilt-lens"
  },
  {
    id: "ICO-009",
    name: "settings",
    componentName: "SettingsIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/settings.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Preferencias y reglas; no rotación perpetua en reposo",
    adaptation: "Giro parcial de engranaje 45deg, 220 ms",
    durationMs: 220,
    gestureType: "rotate-gear"
  },
  {
    id: "ICO-010",
    name: "bell",
    componentName: "BellIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/bell.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Centro de notificaciones; recepción nueva sin robar foco",
    adaptation: "Balanceo ±8 grados una vez, 260 ms",
    durationMs: 260,
    gestureType: "sway-bell"
  },
  {
    id: "ICO-011",
    name: "eye",
    componentName: "EyeIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/eye.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Vista de registros; texto del botón identifica recurso",
    adaptation: "Apertura suave del ojo, 180 ms",
    durationMs: 180,
    gestureType: "eye-open"
  },
  {
    id: "ICO-012",
    name: "eye-off",
    componentName: "EyeOffIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/eye-off.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Visibilidad de contraseña; conservar foco y posición del cursor",
    adaptation: "Transición de trazo de diagonal, 180 ms",
    durationMs: 180,
    gestureType: "stroke-fade"
  },
  {
    id: "ICO-013",
    name: "refresh-cw",
    componentName: "RefreshCwIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/refresh-cw.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Actualizar datos; prevenir solicitudes simultáneas redundantes",
    adaptation: "Giro corto al hover y ciclo continuo solo durante carga, 240 ms",
    durationMs: 240,
    gestureType: "rotate-refresh"
  },
  {
    id: "ICO-014",
    name: "archive",
    componentName: "ArchiveIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/archive.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Maestros archivables; mostrar efecto real y restauración posible",
    adaptation: "Entrada suave de tapa/caja levantando 2 px, 240 ms",
    durationMs: 240,
    gestureType: "lift-lid"
  },
  {
    id: "ICO-015",
    name: "undo",
    componentName: "UndoIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/undo.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Cambios reversibles; no confundir con reembolso financiero",
    adaptation: "Flecha con recorrido corto 2 px a la izquierda, 200 ms",
    durationMs: 200,
    gestureType: "translate-x-left"
  },
  {
    id: "ICO-016",
    name: "redo",
    componentName: "RedoIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/redo.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Edición local o acciones que soporten rehacer explícitamente",
    adaptation: "Recorrido opuesto a deshacer 2 px a la derecha, 200 ms",
    durationMs: 200,
    gestureType: "translate-x-right"
  },
  {
    id: "ICO-017",
    name: "arrow-right",
    componentName: "ArrowRightIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/arrow-right.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Asistentes y navegación; no desplazar texto",
    adaptation: "Traslación 2 px hacia la derecha, 140 ms",
    durationMs: 140,
    gestureType: "translate-x-forward"
  },
  {
    id: "ICO-018",
    name: "arrow-left",
    componentName: "ArrowLeftIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/arrow-left.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Retorno de detalles; preservar filtros",
    adaptation: "Traslación 2 px hacia la izquierda, 140 ms",
    durationMs: 140,
    gestureType: "translate-x-back"
  },
  {
    id: "ICO-019",
    name: "chevron-down",
    componentName: "ChevronDownIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/chevron-down.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Menús y filtros; aria-expanded refleja estado real",
    adaptation: "Giro entre estado colapsado y expandido 180deg, 160 ms",
    durationMs: 160,
    gestureType: "rotate-chevron"
  },
  {
    id: "ICO-020",
    name: "chevron-up",
    componentName: "ChevronUpIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/chevron-up.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Paneles abiertos; conservar foco tras ocultar contenido",
    adaptation: "Giro breve coherente con el panel -180deg, 160 ms",
    durationMs: 160,
    gestureType: "rotate-chevron-reverse"
  },
  {
    id: "ICO-021",
    name: "chevron-right",
    componentName: "ChevronRightIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/chevron-right.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Paginación y jerarquías; disabled al final",
    adaptation: "Traslación corta 2 px a la derecha, 140 ms",
    durationMs: 140,
    gestureType: "translate-x-forward"
  },
  {
    id: "ICO-022",
    name: "chevron-left",
    componentName: "ChevronLeftIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/chevron-left.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Paginación; no reiniciar filtro",
    adaptation: "Traslación corta 2 px a la izquierda, 140 ms",
    durationMs: 140,
    gestureType: "translate-x-back"
  },
  {
    id: "ICO-023",
    name: "circle-help",
    componentName: "CircleHelpIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/circle-help.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Fórmulas, stock y tasas; acceso completo por teclado",
    adaptation: "Pulso leve del signo interrogación, 200 ms",
    durationMs: 200,
    gestureType: "pulse-symbol"
  },
  {
    id: "ICO-024",
    name: "circle-check",
    componentName: "CircleCheckIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/circle-check.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Resultados confirmados; movimiento reducido conserva símbolo",
    adaptation: "Trazar contorno y check, 240 ms",
    durationMs: 240,
    gestureType: "draw-outline-check"
  },
  {
    id: "ICO-025",
    name: "clock",
    componentName: "ClockIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/clock.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Timeline y tareas; evitar apariencia de progreso inventado",
    adaptation: "Giro parcial de manecilla 45deg, 240 ms",
    durationMs: 240,
    gestureType: "rotate-hand"
  },
  {
    id: "ICO-026",
    name: "calendar-days",
    componentName: "CalendarDaysIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/calendar-days.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Filtros y fechas; no cambiar selección por gesto",
    adaptation: "Resaltado breve de una celda con opacidad, 180 ms",
    durationMs: 180,
    gestureType: "highlight-cell"
  },
  {
    id: "ICO-027",
    name: "users",
    componentName: "UsersGroupIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/users.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Navegación de CRM y empleados",
    adaptation: "Separación leve de siluetas 1 px, 200 ms",
    durationMs: 200,
    gestureType: "spread-avatars"
  },
  {
    id: "ICO-028",
    name: "user-plus",
    componentName: "UserPlusIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/user-plus.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Invitaciones; mostrar límite de permisos",
    adaptation: "Pulso del signo más 1.1x, 180 ms",
    durationMs: 180,
    gestureType: "pulse-badge"
  },
  {
    id: "ICO-029",
    name: "cart",
    componentName: "CartIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/cart.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Registro de venta y pedido; anunciar cantidad por texto",
    adaptation: "Desplazamiento horizontal 2 px, 200 ms",
    durationMs: 200,
    gestureType: "translate-x-wheel"
  },
  {
    id: "ICO-030",
    name: "box",
    componentName: "BoxIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/box.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Catálogo y detalle; usar el mismo símbolo para la misma entidad",
    adaptation: "Movimiento breve de tapa, 220 ms",
    durationMs: 220,
    gestureType: "box-lid"
  },
  {
    id: "ICO-031",
    name: "boxes",
    componentName: "BoxesIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/boxes.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Almacenes y existencias; evitar animar todas las tarjetas",
    adaptation: "Resaltado secuencial contenido, 240 ms",
    durationMs: 240,
    gestureType: "sequential-highlight"
  },
  {
    id: "ICO-032",
    name: "credit-card",
    componentName: "CreditCardActionIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/credit-card.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Métodos y pago; éxito solo desde estado confirmado",
    adaptation: "Desplazamiento leve de franja 1 px, 220 ms",
    durationMs: 220,
    gestureType: "shift-stripe"
  },
  {
    id: "ICO-033",
    name: "wallet",
    componentName: "WalletIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/wallet.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Caja, cuentas por cobrar y resumen financiero",
    adaptation: "Apertura corta de solapa, 220 ms",
    durationMs: 220,
    gestureType: "open-flap"
  },
  {
    id: "ICO-034",
    name: "chart-line",
    componentName: "ChartLineIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/chart-line.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Navegación Analytics; no animar cifras con cada render",
    adaptation: "Dibujar línea una vez, 260 ms",
    durationMs: 260,
    gestureType: "draw-trend-line"
  },
  {
    id: "ICO-035",
    name: "chart-column-increasing",
    componentName: "ChartColumnIncreasingIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/chart-column-increasing.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Vendedores y categorías; barras de icono no son datos reales",
    adaptation: "Crecimiento breve de barras 1.0->1.15->1.0, 260 ms",
    durationMs: 260,
    gestureType: "grow-bars"
  },
  {
    id: "ICO-036",
    name: "chart-pie",
    componentName: "ChartPieIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/chart-pie.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Análisis de mezcla; proporciones reales se presentan en gráfico",
    adaptation: "Resaltado de segmento con leve rotación 15deg, 220 ms",
    durationMs: 220,
    gestureType: "rotate-slice"
  },
  {
    id: "ICO-037",
    name: "file-text",
    componentName: "FileTextIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/file-text.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Reportes, comprobantes y plantillas",
    adaptation: "Dibujar líneas internas secuencialmente, 220 ms",
    durationMs: 220,
    gestureType: "draw-doc-lines"
  },
  {
    id: "ICO-038",
    name: "logout",
    componentName: "LogoutActionIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/logout.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Perfil; cerrar en servidor antes de volver a login",
    adaptation: "Flecha de salida 2 px a la derecha, 180 ms",
    durationMs: 180,
    gestureType: "translate-x-exit"
  },
  {
    id: "ICO-039",
    name: "lock",
    componentName: "LockIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/lock.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Periodos cerrados y permisos; explicar motivo",
    adaptation: "Movimiento vertical del arco de bloqueo 2 px, 200 ms",
    durationMs: 200,
    gestureType: "shackle-click"
  },
  {
    id: "ICO-040",
    name: "shield-check",
    componentName: "ShieldCheckIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/shield-check.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "MFA y aprobaciones; no comunicar certificación inexistente",
    adaptation: "Dibujar check central dentro de escudo, 220 ms",
    durationMs: 220,
    gestureType: "draw-shield-check"
  },
  {
    id: "ICO-041",
    name: "moon",
    componentName: "MoonIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/moon.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Selector de tema sin destello",
    adaptation: "Rotación mínima 15deg con fundido, 200 ms",
    durationMs: 200,
    gestureType: "rotate-fade-moon"
  },
  {
    id: "ICO-042",
    name: "sun",
    componentName: "SunIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/sun.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Selector de tema; no animación continua",
    adaptation: "Giro parcial de rayos 45deg, 200 ms",
    durationMs: 200,
    gestureType: "rotate-sun-rays"
  },
  {
    id: "ICO-043",
    name: "menu",
    componentName: "MenuIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/menu.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Navegación móvil; estado expandido accesible",
    adaptation: "Desplazar líneas alternadas 1 px y volver, 160 ms",
    durationMs: 160,
    gestureType: "shift-burger-bars"
  },
  {
    id: "ICO-044",
    name: "external-link",
    componentName: "ExternalLinkIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/external-link.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Enlaces externos y ayuda; abrir en pestaña segura con rel noopener",
    adaptation: "Flecha diagonal 1.5 px hacia noreste, 180 ms",
    durationMs: 180,
    gestureType: "translate-diagonal"
  },
  {
    id: "ICO-045",
    name: "send",
    componentName: "SendActionIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/send.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Envío de facturas y mensajes",
    adaptation: "Inclinación de avioncito 5deg y leve desplazamiento hacia adelante, 180 ms",
    durationMs: 180,
    gestureType: "airplane-launch"
  },
  {
    id: "ICO-046",
    name: "attach-file",
    componentName: "AttachFileIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/paperclip.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Adjuntar archivos en comprobantes y gastos",
    adaptation: "Rotación suave de clip 10deg, 180 ms",
    durationMs: 180,
    gestureType: "rotate-clip"
  },
  {
    id: "ICO-047",
    name: "link",
    componentName: "LinkChainIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/link.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Vinculación de órdenes y transacciones",
    adaptation: "Aproximación de eslabones 1 px, 180 ms",
    durationMs: 180,
    gestureType: "join-links"
  },
  {
    id: "ICO-048",
    name: "grip-vertical",
    componentName: "GripVerticalIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/grip-vertical.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Reordenar columnas y campos arrastrables",
    adaptation: "Ligera expansión de puntos táctiles 1.1x, 160 ms",
    durationMs: 160,
    gestureType: "scale-dots"
  },
  {
    id: "ICO-049",
    name: "expand",
    componentName: "ExpandIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/expand.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Pantalla completa y detalle ampliado",
    adaptation: "Flechas diagonales separándose 1.5 px hacia afuera, 180 ms",
    durationMs: 180,
    gestureType: "spread-corners"
  },
  {
    id: "ICO-050",
    name: "minimize",
    componentName: "MinimizeIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/minimize.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Reducir panel o salir de pantalla completa",
    adaptation: "Flechas diagonales convergiendo 1.5 px hacia adentro, 180 ms",
    durationMs: 180,
    gestureType: "converge-corners"
  },
  {
    id: "ICO-051",
    name: "truck",
    componentName: "TruckIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/truck.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Despacho y guías de remisión",
    adaptation: "Desplazamiento horizontal de camión 2 px y giro de ruedas, 220 ms",
    durationMs: 220,
    gestureType: "roll-truck"
  },
  {
    id: "ICO-052",
    name: "badge-percent",
    componentName: "BadgePercentIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/badge-percent.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Descuentos comerciales y promociones",
    adaptation: "Rotación suave de insignia 10deg, 200 ms",
    durationMs: 200,
    gestureType: "tilt-badge"
  },
  {
    id: "ICO-053",
    name: "trash-2",
    componentName: "Trash2Icon",
    originalUrl: "https://animateicons.in/icons/lucide/trash-2",
    version: "main-2026.10",
    license: "MIT",
    application: "Eliminar registros con aviso destructivo",
    adaptation: "Apertura de tapa de tachito -18deg y sacudida breve, 240 ms",
    durationMs: 240,
    gestureType: "lift-trash-lid"
  },
  {
    id: "ICO-054",
    name: "trash",
    componentName: "TrashIcon",
    originalUrl: "https://animateicons.in/icons/lucide/trash",
    version: "main-2026.10",
    license: "MIT",
    application: "Eliminación simple de línea o borrador",
    adaptation: "Vibración contenida de papelera ±4deg, 220 ms",
    durationMs: 220,
    gestureType: "shake-can"
  },
  {
    id: "ICO-055",
    name: "fallback",
    componentName: "FallbackCatalogIcon",
    originalUrl: "https://github.com/pqoqubbw/icons/blob/main/icons/circle-dot.tsx",
    version: "main-2026.10",
    license: "MIT",
    application: "Iconos auxiliares o no catalogados explícitamente",
    adaptation: "Pulsación contenida de escala 1.05x y retorno, 180 ms",
    durationMs: 180,
    gestureType: "pulse-point"
  }
];

export function getIconRegistryEntry(idOrName: string): IconRegistryEntry | undefined {
  const query = idOrName.toLowerCase().trim();
  return ICON_DEPENDENCY_REGISTRY.find(
    (item) =>
      item.id.toLowerCase() === query ||
      item.name.toLowerCase() === query ||
      item.componentName.toLowerCase() === query
  );
}

export function getAllIconRegistryEntries(): IconRegistryEntry[] {
  return [...ICON_DEPENDENCY_REGISTRY];
}
