# Pendientes del proyecto

Estado al 2026-10-03. La knowledge base quedó revisada y ampliada para implementar el proyecto completo; la fundación está detenida en el paso del roadmap (`CHANGES.md` todavía no existe).

Este archivo es una lista de trabajo. Cuando un punto se cierre, se borra de acá; las decisiones quedan registradas en `knowledge-base/10_preguntas_abiertas.md`.

## 1. Para leer o revisar personalmente

Lo que sigue fue redactado por el agente y todavía no lo leyó el autor.

- [ ] **Criterios de aceptación propuestos** en `knowledge-base/06_funcionalidades.md`, marcados como "criterios propuestos por el agente, a revisar por el autor":
  - US-014 marcar atendido o ausente
  - US-021 lista de espera
  - US-051 retención o devolución de seña
  - US-060 ficha del paciente
  - US-061 presupuesto simple
  - US-062 registro de pago
  - US-070 consentimiento
  - US-080 reportes
- [ ] **Reglas nuevas** en `knowledge-base/05_reglas_de_negocio.md`: RN-AG-12, RN-AG-13, RN-LE-05, RN-LE-06, RN-SP-09, RN-FC-05, RN-RP-01 a RN-RP-03, RN-GL-04.
- [ ] **Épica 10, Usuarios y acceso** (US-090 a US-094) en `06_funcionalidades.md`: historias nuevas completas.
- [ ] **Modelo de datos completo** en `knowledge-base/04_modelo_de_datos.md`, incluida la sección final "Propuestas aceptadas y Suposiciones pendientes".
- [ ] **Texto del consentimiento**: solo está definido que es un borrador no validado legalmente; el contenido no está redactado.

### Suposiciones del agente sin confirmar

Agregadas en la última pasada; ninguna bloquea el roadmap.

- [ ] La entrada de lista de espera tiene un token propio para que el paciente se retire desde un link.
- [ ] La versión vigente del texto de consentimiento es una constante de la aplicación.
- [ ] Un pago se anula sin reemplazo con un registro que lo corrige y `pagado` en falso.
- [ ] Un turno en `pendiente_sena` o `pendiente_aprobacion` no puede marcarse atendido ni ausente.
- [ ] "Fuera de plazo" significa `ahora > inicio − antelación de cancelación`.

### Suposiciones anteriores que siguen marcadas

- [ ] RN-AG-10d: turnos que cruzan la medianoche.
- [ ] RN-LE-02: la lista de espera se atiende por orden de llegada.
- [ ] RN-TD-03: el consultorio puede cancelar desde el panel en cualquier momento.
- [ ] RN-TD-04: la reprogramación conserva la seña.
- [ ] RN-PR-05: exportación de datos.
- [ ] `03_actores_y_roles.md`: el historial no se muestra al paciente.
- [ ] `08_arquitectura_propuesta.md`: logs, límite de peticiones y nombres de variables de entorno.
- [ ] `11_integraciones_whatsapp_y_mercadopago.md`: devolución real por API y túnel HTTPS para el webhook.

## 2. Pasos que siguen

- [ ] **Roadmap** (`CHANGES.md`), etapa 4 de la consigna. Las restricciones ya están armadas y guardadas en Engram (tema `opsx/foundation/roadmap-restricciones`). Revisar que quede alineado con el MVP de la sección D del informe.
- [ ] **Skills y reglas del agente**, etapa 5: recomendación de skills, `.atl/skill-registry.md`, `CLAUDE.md` y `AGENTS.md`. Incluir como regla propia del dominio la de datos ficticios (RN-PR-01).
- [ ] **Ciclo OPSX del primer change**, etapa 6: crear turno sin solapamientos (explore, propose, apply, verify, archive). Escenarios E1 a E7 y E12.
- [ ] **Evidencia de Engram**, etapa 7.

## 3. Se decide más adelante, en el change que corresponda

| Tema | Cuándo |
|---|---|
| Versiones exactas de las dependencias (P-17) | Design del primer change |
| Código y estado HTTP del recurso inexistente (RN-GL-04, 422), nombres del contrato, tests de API | Design del primer change |
| Duración de la sesión, renovación y algoritmo de hash | Change de usuarios y acceso |
| Alembic, restricción de exclusión y prueba de reservas simultáneas (E11) | Change de infraestructura con PostgreSQL, antes de la reserva online |
| Destino de un turno pendiente de aprobación que el odontólogo rechaza | Change de reserva online |
| Vencimiento del token de gestión del turno | Change de reserva online |
| Estructura de las preferencias de la lista de espera y criterio de compatibilidad | Change de lista de espera |
| Reportes: denominador cero, filtro por profesional, franjas con vigencia | Change de reportes |
| Uso de Redis en la v1 y estados de los mensajes | Change de recordatorios |

## 4. Entregables de la consigna a cargo del autor

- [ ] Bitácora y **reflexión escrita** (1 a 2 páginas), que es un entregable aparte del informe. Material del 2026-10-03: comparación con la documentación de un proyecto anterior y los ajustes que salieron de ahí.
- [ ] Capturas para el **video de defensa**: instalador de Active Stack, revisión del spec en Propose, tests en verde, endpoint en Swagger, consulta a Engram.
- [ ] `README.md` con los pasos para clonar, instalar y correr los tests.
- [ ] Regenerar el PDF del informe si cambia: `node docs/discovery/generar-pdf.mjs`.

## 5. Diferido fuera de la v1

| Tema | Destino |
|---|---|
| API oficial de WhatsApp (P-04, P-05, P-06) | Fase 2 |
| Sobreturnos, excepción de horario, interfaz con varios sillones, división de pagos | Fase 2 |
| Obras sociales (P-07), odontograma completo | v1.1 |
| Imágenes, ARCA, caja completa | v2 |
| Google Calendar, API pública, devolución real por API de Mercado Pago | Posterior |
| Precio a publicar (P-15) | Sin fecha |
| Validez legal de la seña, registro ante la AAIP y consentimiento (P-01, P-02, P-03) | Requiere revisión legal antes de un uso real |
| Reportes (US-080) | Dentro de la v1 como último change, marcado como extensión fuera del MVP del informe |
