# Flujo de Procesos: Synapse Data Hub

Bienvenido al documento explicativo de los flujos de creación, revisión y cierre de tareas que corren bajo el ecosistema de Synapse Data Hub de Lº Bueno Group. A continuación, se detalla el ciclo de vida completo de una solicitud en la plataforma.

## 1. Creación PENDIENTE (User Viewer)
Un empleado o cliente entra al apartado `📝 Nueva Solicitud`.
- Completa el formulario de categorización, especificando Contexto de Negocio, KPIs Esperados y Uso del Dato.
- Al seleccionar la categoría y el nivel de complejidad (SLA Antigravity Levels 1 al 6), se hace un cálculo transparente que asigna un tiempo máximo estimado y una **Fecha Límite** objetiva base para reportar.
- Con clic en *Enviar*, el registro viaja a la Google Sheet (`REQUESTS`) como estado **PENDIENTE** y SendGrid dispara la notificación de recibido al correo.

## 2. Recepción y Triaje (Dashboard de Operaciones)
Los usuarios Administradores y Operaciones visualizan el nuevo ticket en el `📊 Dashboard`.
- Evalúan la descripción general desde el **Expander de Detalles**.
- Si la tarea carece de contexto suficiente para trabajarla (ej. no se entiende un KPI o falta un acceso), la **Detienen y Piden Aclaración** cambiando el estado a *Esperando Info*. Un correo advierte de esta situación al creador original. Mismas acciones pueden hacerse para Reprogramar *Deadlines* si un SLA es subestimado.

## 3. Asignación Activa (EN PROGRESO)
Cuando la solicitud fue depurada, el perfil Owner/Admin se dirige a la pestaña `👥 Asignar`.
- **Match de equipo:** El sistema muestra una lista desplegable con los Ops disponibles, cruzado contra las "Horas requeridas semanales" en `📋 Equipo`, asegurando que nadie tenga más de 40 horas al límite (Control de *burnout*).
- Al guardar, la tarea escala al status **EN PROGRESO**, inscribiéndose en la hoja `WEEKLY_ASSIGNMENTS` y mandando un aviso en tiempo real al Analista asignado para que empiece el Delivery.

## 4. Desarrollo y Checkpoint (EN REVISIÓN)
El analista (asignado) procede a trabajar conectándose a bases o desarrollando en Python/BI.
- Al completarla, en su pestaña de `🎯 Mis Tareas` aparecerá un formulario para anexar URL de los Dashboards, Notebooks o Documentos construidos, acompañados del racional.
- Se hace clic en "Enviar a Revisión". El ticket muta a **EN REVISIÓN** avisando al Owner y Líder del proyecto que el trabajo está listo para escrutinio.

## 5. Finalización / Reproceso
En el `📊 Dashboard`, el Data Lead puede mirar el entregable desde la plataforma.
- **Si el entregable es correcto:** Hacer clic en "Marcar Solicitud como COMPLETADA". Notificación de finalización enviada al cliente.
- **Si el entregable requiere re-work:** Registra el concepto en la sección de "Reprocesos", añade las horas adición consumidas y la tarea repite la parte tardía del ciclo de atención.
