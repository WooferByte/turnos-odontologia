# Informe de Discovery

## Sistema de gestión de turnos y agenda para consultorios odontológicos (mercado argentino)

| | |
|---|---|
| **Materia** | Metodología I – Tecnicatura Universitaria en Programación |
| **Trabajo** | Trabajo de Integración: del Discovery al primer Change (Etapa 2, Discovery) |
| **Integrante** | [Nombre del autor] |
| **Fecha** | 2026-10-01 |
| **Insumos** | 31 notas de relevamiento en `discovery/sources/*.md` (primera pasada y segunda pasada del 2026-10-01; la segunda prevalece) |

---

## Resumen ejecutivo

**Qué se investigó.** Se relevaron 31 sistemas que permiten gestionar turnos y agenda de pacientes odontológicos: 13 argentinos (9 con módulo odontológico y 4 agendas multirrubro), 9 latinoamericanos o hispanohablantes y 9 internacionales de referencia. Todas las fuentes se consultaron el 2026-10-01. Se usaron sitios oficiales, páginas de precios, centros de ayuda, políticas de privacidad, fichas de tiendas de aplicaciones y, en pocos casos, reseñas de terceros. En una segunda pasada se profundizó en cinco sistemas y se sumaron tres (Naclix, Neocita, Ulifeon). Esa pasada corrigió varias afirmaciones de la primera.

**Hallazgos principales.**

1. **La evidencia es mayormente comercial.** Solo Open Dental tiene confianza alta (manual y API documentados). Los sistemas argentinos mejor puntuados (Naclix 3,75; DentalCore 3,65; Bilog y ClinIA 3,15) se apoyan sobre todo en afirmaciones comerciales [AC]. Lo comprobado [C] se limita en general a precios, políticas de privacidad y algunas páginas de ayuda.
2. **WhatsApp es estándar, pero ningún competidor documenta la API oficial de WhatsApp Business.** DentalCore declara expresamente que no la usa (sesión por QR). Bilog envía los recordatorios en forma manual o semiautomática. Neocita usa un enlace en su plan gratuito. En Dentalink es un servicio adicional pago y no se indica el mecanismo. Naclix y Doctocliq lo sugieren ("canal oficial", "Meta Business Partner") pero no lo documentan. Por lo tanto, un recordatorio semiautomático por enlace `wa.me` está **a la par del mercado**, no por debajo.
3. **La lista de espera ya existe en el mercado local, aunque poco documentada.** Naclix declara una lista de espera con aviso automático al siguiente paciente, además de sobreturnos [AC]. DentalCore declara que su bot ofrece los huecos cancelados [AC]. El relleno documentado de huecos sigue siendo patrimonio de Open Dental y Dentally [C].
4. **Hay vacíos de reglas de agenda.** Ningún sistema evidencia horarios recurrentes configurables con excepciones. La prevención de solapamientos solo aparece como afirmación comercial (Órbita, por sillón; EXACT). La reprogramación por el propio paciente solo está comprobada en Dentally. La trazabilidad de cambios de turno solo aparece en Naclix.
5. **La facturación y las integraciones locales son el diferencial de los sistemas clínicos argentinos** (ARCA, obras sociales, Mercado Pago). Las agendas multirrubro (Turnito, SimpleTurno, Neocita, Ulifeon) compiten por precio y por la seña con Mercado Pago, pero no tienen clínica odontológica.

**MVP recomendado.** Producto para el **odontólogo independiente** (1 profesional, 1 sillón modelado como recurso). El núcleo es una agenda confiable: duraciones por prestación, horario recurrente con bloqueos, prevención de solapamientos por profesional y por sillón, y reserva 24/7 por enlace. Se suman confirmación por WhatsApp (API oficial en modo prueba, con `wa.me` semiautomático como alternativa), cancelación y reprogramación por el paciente, seña con Mercado Pago (Checkout Pro), lista de espera, trazabilidad de cambios y una ficha clínica mínima con presupuestos y registro de pagos simples. Los diferenciadores son la lista de espera que ofrece huecos por WhatsApp, el horario recurrente con trazabilidad y el precio publicado en ARS. El odontograma completo, las obras sociales, ARCA y el uso de la API oficial de WhatsApp en producción quedan para etapas posteriores.

---

## Datos de contexto del mercado

Las cifras siguientes sirven solo para dimensionar el mercado; ninguna se usa como hecho de diseño. Cada una tiene una advertencia sobre su alcance.

| Dato | Fuente y URL | Advertencia |
|---|---|---|
| 85% de los odontólogos encuestados atiende en consultorio propio y 54% lo comparte | Dental Tribune Latinoamérica, encuesta durante la pandemia de covid-19 (n=313). https://la.dental-tribune.com/news/jornada-de-actualizacion-en-odontologia-2/ | Muestra no probabilística, contexto de pandemia: indica tendencia, no proporción poblacional. |
| 53.011 odontólogos en Argentina | Censo Nacional Económico (INDEC), citado por UNCuyo/La Nación. https://www.uncuyo.edu.ar/prensa/la-nacion-los-odontologos-se-ven-enfrentados-a-una-compleja-realidad-laboral | Fuente secundaria (nota de prensa); no se consultó el dato original del INDEC. |
| 68% lleva la historia clínica en papel y 66% no usa software de diagnóstico y diseño de tratamientos (no mide software de gestión de turnos) | Artículo indexado en RePEc (n=100, CABA y GBA, 2024). https://ideas.repec.org/a/cwf/dentar/dent2025127.html | Muestra chica y concentrada en el AMBA; no extrapolable al país. |
| 1.728 clínicas dentales en Argentina | Listado de *scraping* comercial (Rentech Digital). https://rentechdigital.com/smartscraper/ru/business-report-details/list-of-dental-clinics-in-argentina | Fuente comercial sin metodología pública: solo orden de magnitud. |
| 10,9 dentistas por cada 10.000 habitantes | OMS, citado por Ámbito. https://www.ambito.com/informacion-general/dia-del-odontologo-argentina-es-uno-los-paises-mayor-proporcion-dentistas-el-mundo-segun-la-oms-n6197981 | Año del dato no indicado; fuente secundaria. |

**Lectura.** Predomina el consultorio propio, a menudo compartido, y es baja la digitalización declarada. Eso respalda el segmento "odontólogo independiente" y una adopción sencilla. Se descartaron dos cifras que circulaban en borradores: un "3% de adopción tecnológica" (la tesis citada no lo contiene) y un "ausentismo de 60-70%" (sin fuente).

---

## Convenciones de evidencia

| Marca | Significado |
|---|---|
| **[C] Comprobado** | Visto en documentación, centro de ayuda, página de precios, política de privacidad, términos o ficha de tienda oficial. La función aparece descrita con detalle verificable. |
| **[AC] Afirmación comercial** | Declarado en páginas de marketing del proveedor, sin demostración ni documentación. |
| **No evidenciado** | No aparece en las páginas leídas. No significa que no exista: significa que no pudo constatarse. |
| **[3ro]** | Fuente de terceros (Capterra, comparativas). Las comparativas publicadas por competidores se consideran sesgadas. |

---

## A. Tabla comparativa

**Orden por relevancia para Argentina:** (1) argentinos con módulo odontológico; (2) agendas argentinas multirrubro; (3) latinoamericanos e hispanohablantes; (4) internacionales de referencia. Dentro de cada grupo, por cercanía al caso de uso. Todas las fuentes se consultaron el **2026-10-01**. Las URL específicas de cada afirmación figuran en la sección "Referencias".

### A.1 Identidad, modelo comercial y fuente

| # | Producto / Proveedor | País · Segmento | Modalidad | Modelo comercial | Adopción declarada | URL oficial · fecha | Confianza |
|---|---|---|---|---|---|---|---|
| **G1** | **Argentina, con módulo odontológico** ||||||||
| 1 | **DentalCore** / DentalCore | Argentina (La Plata) · consultorio a clínica | SaaS nube; app móvil No evidenciado | USD 50/mes con 2 usuarios + USD 10 por usuario adicional [C]; **sin prueba gratis: garantía de reembolso de 14 días** [C] | No evidenciado | https://dentalcore.app/ · 2026-10-01 | Medio |
| 2 | **Bilog** / BILOG S.R.L. | Argentina (Buenos Aires) · consultorio y clínica, multisucursal | SaaS nube; app iOS [C]; Android sin ficha legible | Freemium gratis + Lite y Premium por usuario, **sin precio publicado** [C]; sin permanencia [C] | +1.500 clínicas, +5.000 usuarios [AC] | https://bilog.com.ar/ · 2026-10-01 | Medio |
| 3 | **Naclix** / Mariano P. Rebord Palazzo (unipersonal) | Argentina · **multirrubro de salud** (odontología es un rubro más) | SaaS web + app iOS [C] | Gratuito + 30 días Pro; Inicio ARS 9.800, Profesional ARS 39.800, Negocio ARS 89.000 por mes [C] | No evidenciado ("17 países" por banderas [AC]) | https://naclix.com/ · 2026-10-01 | Medio |
| 4 | **ClinIA** (Odontología) / ClinIA | Argentina · consultorio a redes de sucursales | Plataforma web [AC] | No evidenciado (demo gratuita [AC]) | "Cientos de odontólogos" [AC] | https://www.clinia.com.ar/odontologia · 2026-10-01 | Bajo |
| 5 | **Órbita** / Órbita Global | Argentina (La Plata) · clínica y multiespecialidad | SaaS con IA [AC] | No evidenciado | 8+ clientes nombrados [AC] | https://hiorbita.com/ · 2026-10-01 | Bajo |
| 6 | **Sigo** / Sigo | Argentina (Bahía Blanca) · independiente y clínica | SaaS nube [AC] | ARS 25.000/mes o ARS 250.000/año; prueba 30 días [AC, precio publicado] | No evidenciado | https://sigo.com.ar/ · 2026-10-01 | Bajo |
| 7 | **OdontoGRAMA** / Solsoftware | Argentina · consultorio multiusuario | SaaS nube [AC] | "Versión gratuita completa" [AC]; planes pagos No evidenciado | No evidenciado | https://odontograma.com.ar/ · 2026-10-01 | Bajo |
| 8 | **OdontoSoft Millennium** / GB Systems | Argentina y EE. UU. · consultorio y clínica | Escritorio Windows; módulo web opcional | Licencia USD 299 a 1.199 o USD 35/65/99 por mes; módulo web USD 120 [C] | "+3.000" dentistas y clínicas [AC] | https://gbsystems.com/os/ · 2026-10-01 | Bajo |
| 9 | **OdontoApp** / OdontoApp | Argentina · consultorio pequeño | No evidenciado | Sección de planes existe; precios No evidenciado | "Más de 10 odontólogos" [AC] | https://odontoapp.com.ar/ · 2026-10-01 | Bajo |
| **G2** | **Argentina, agendas multirrubro** ||||||||
| 10 | **Turnito** / Turnito | No evidenciado (precios en ARS, sitio /ar) · **agenda multirrubro, no odontológica** | SaaS | Gratis (100 reservas/mes, comisión 5%); Plus ARS 12.000, Advance ARS 24.500, Pro ARS 42.000 por mes con IVA [C] | 4,8 con 142 reseñas Google [AC]; "40.000 usuarios" **no verificado** | https://turnito.app/ · 2026-10-01 | Medio |
| 11 | **SimpleTurno** / SimpleTurno | Argentina · independiente, multirrubro | SaaS en navegador, sin app [C] | Gratis (1 profesional, recordatorios solo por email) [C]; Pro ARS 12.900/mes [C] | No evidenciado | https://simpleturno.com/ · 2026-10-01 | Medio |
| 12 | **Neocita** / Neocita | Argentina (dirección en La Plata no verificada) · multirrubro | Web + app **solo Android** | Gratis (1 agenda, 30 clientes, 50 turnos/mes); pago ARS 5.900/mes; recordatorios automáticos ARS 6.000 a 24.000 + IVA por mes [C] | "Cientos de personas" [AC]; "100K+ descargas" no verificado | https://www.neocita.com/ · 2026-10-01 | Medio |
| 13 | **Ulifeon** / Ulifeon S.A.S. | Argentina (inferido) · profesionales de salud + marketplace de pacientes | App iOS/Android + link | Gratis para el profesional; **el paciente paga 2,2% + IVA** [AC] | 4,0 con 4 calificaciones en App Store [C] | https://ulifeon.com/ · 2026-10-01 | Bajo |
| **G3** | **Latinoamérica e hispanohablantes** ||||||||
| 14 | **Dentalink** / Healthatom | Chile · clínicas y cadenas. **Referente regional, no local**: /ar sin datos argentinos [C] | SaaS web + Android/iOS [3ro] | Esencial/Pro/Titanium sin precio [C]; USD 29/usuario/mes según Capterra [3ro] | 15.000+ clientes [AC] | https://www.softwaredentalink.com/ · 2026-10-01 | Medio |
| 15 | **AgendaPro** (Dental) / AgendaPro Inc. | Chile · 2 a 20 profesionales, multirrubro | SaaS nube | USD 9/29/59/199 por mes; WhatsApp add-on desde USD 7/mes [C] | 135.000+ profesionales [AC] | https://agendapro.com/es/dental/software-odontologico · 2026-10-01 | Medio |
| 16 | **Doctocliq** / Doctocliq | Perú (inferido) · independiente a clínica | SaaS nube | Gratis (1 doctor, 30 pacientes/mes); USD 19/29/49 por mes [C] | 4.000+ médicos [AC] | https://www.doctocliq.com/ · 2026-10-01 | Medio |
| 17 | **Dentidesk** / Dentidesk | Chile · odontólogos y clínicas | SaaS nube + app | No publicado; prueba 15 días (30 según terceros) | 3 testimonios | https://www.dentidesk.com/ · 2026-10-01 | Medio |
| 18 | **Odontosys** / Odontosys | Uruguay · clínicas hispanohablantes | Web + apps [AC] | No evidenciado (demo) | +400 usuarios [AC] | https://odontosys.com/ · 2026-10-01 | Bajo |
| 19 | **Clinicorp** / Clinicorp | Brasil · consultorio y clínica | SaaS nube | R$ 159,90 y R$ 369,90 por mes [C] | No evidenciado | https://www.clinicorp.com/ · 2026-10-01 | Medio |
| 20 | **Dentrisoft** / Dentrisoft | Colombia · odontólogos y clínicas | SaaS nube | COP 89.900 / 169.900; prueba 14 días [AC, precio publicado] | +500 odontólogos [AC] | https://dentrisoft.com/ · 2026-10-01 | Bajo |
| 21 | **DtDental** / DtDental | Colombia · consultorio y clínica | SaaS nube | No evidenciado (demo) | +10.000 profesionales [AC] | https://dtdental.co/ · 2026-10-01 | Bajo |
| 22 | **OdontoSoft** / OdontoSoft | Perú · consultorio a clínica | Híbrido local/nube [C] | Local S/ 349; Cloud desde S/ 59/mes; gratis hasta 30 pacientes [C] | No evidenciado | https://odontosoft.me/ · 2026-10-01 | Bajo |
| **G4** | **Internacionales (referencia)** ||||||||
| 23 | **Odontonet** / Informática Dental (Nubentia S.L.) | España · clínicas | Escritorio + nube gestionada | No evidenciado | No evidenciado | https://informaticadental.com/odontonet/ · 2026-10-01 | Bajo |
| 24 | **Open Dental** / Open Dental Software | EE. UU. (inferido) · consultorio y multi-local | Servidor local + API | USD 199/mes por ubicación, contrato 12 meses [C] | No evidenciado | https://www.opendental.com/ · 2026-10-01 | **Alto** |
| 25 | **Dentally** / Henry Schein One UK | Reino Unido · consultorios | Nube | No evidenciado | No evidenciado | https://www.dentally.com/en-gb/ · 2026-10-01 | Medio |
| 26 | **EXACT** / Software of Excellence | UK/AU/NZ · consultorios | Nube con instalación remota | No evidenciado | "Miles de consultorios" [AC] | https://www.exactdental.com.au/ · 2026-10-01 | Bajo |
| 27 | **Dentrix / Ascend** / Henry Schein One | EE. UU. (inferido) · consultorio y multi-local | Local y nube | No evidenciado | 35.000+ consultorios [AC] | https://www.dentrix.com/ · 2026-10-01 | Bajo |
| 28 | **Curve Dental** / CD Newco, LLC | EE. UU. · consultorios EE. UU./Canadá | Nube | No evidenciado | 100.000+ usuarios [AC] | https://www.curvedental.com/ · 2026-10-01 | Bajo |
| 29 | **Denticon** / Planet DDS | EE. UU. · DSO y grupos | Nube | No evidenciado | 13.000+ consultorios [AC] | https://www.planetdds.com/denticon/ · 2026-10-01 | Bajo |
| 30 | **tab32** / tab32 | EE. UU. · consultorios chicos y DSO | Nube | USD 125/mes año 1, USD 225/mes desde año 2; cargos por uso [C] | 1.000+ consultorios [AC] | http://tab32.com/ · 2026-10-01 | Bajo |
| 31 | **Weave** / Weave Communications | EE. UU. · salud y pymes (no es software de gestión clínica) | SaaS | No evidenciado | No evidenciado | https://www.getweave.com/ · 2026-10-01 | Bajo |

### A.2 Agenda, turnos digitales y automatización

| # | Producto | Agenda (sillones, duración, bloqueos, sobreturnos, solapamiento) | Reserva, cancelación y lista de espera | WhatsApp y recordatorios | Fuente principal · fecha |
|---|---|---|---|---|---|
| 1 | DentalCore | Multiprofesional, *drag and drop* [AC]; sillones, bloqueos, sobreturnos y anti-solapamiento: No evidenciado | Portal 24/7 [AC]; el bot ofrece los huecos cancelados [AC]; cancelación por el paciente y lista de espera formal: No evidenciado ("waiting room" es la sala de espera) | **Sesión por QR, no API oficial** (cita literal del sitio); 9 automatizaciones con confirmación SÍ/NO [AC] | dentalcore.app y /pricing · 2026-10-01 |
| 2 | Bilog | Por profesional y sillón [AC]; **"nuevo sobreturno"** y estados de turno [C]; duración, solapamiento y recurrencia: No evidenciado | Reserva por link y QR con DNI + email [C]; cancelación opcional con ventana mínima [C]; reprogramación y lista de espera: No evidenciado | **Envío manual/semiautomático, no se programa solo**; masivo con módulo adicional; confirmación por palabra clave [C] | docs.bilog.com.ar · 2026-10-01 |
| 3 | Naclix | **Sobreturnos** marcados [AC]; bloqueos, anti-solapamiento y recurrencia: No evidenciado | Reserva 24/7 [AC]; **lista de espera con aviso automático** [AC]; cancelación por el paciente: No evidenciado | Recordatorios 24 h/3 h/1 h con confirmación [AC]; "canal oficial, tu mismo número" [AC] (mecanismo no documentado) | naclix.com · 2026-10-01 |
| 4 | ClinIA | Por profesional, especialidad o sillón [AC]; resto No evidenciado | Agenda online 24/7, reagendamiento [AC]; lista de espera: No evidenciado | Confirmación WhatsApp/email [AC] | clinia.com.ar/odontologia · 2026-10-01 |
| 5 | Órbita | Por sillón y profesional; **"no permite dos pacientes en el mismo sillón"** [AC] | Reserva online [AC]; lista de espera: No evidenciado | Asistente IA en WhatsApp que agenda; recontacto [AC] | hiorbita.com · 2026-10-01 |
| 6 | Sigo | Multiprofesional, duración por turno [AC] | No evidenciado | Recordatorios por email [AC]; WhatsApp: No evidenciado | sigo.com.ar · 2026-10-01 |
| 7 | OdontoGRAMA | Agendas personalizables [AC] | No evidenciado | No evidenciado | odontograma.com.ar · 2026-10-01 |
| 8 | OdontoSoft Millennium | Agenda de citas [AC] | No evidenciado | SMS masivos [AC]; WhatsApp: No evidenciado | gbsystems.com/os · 2026-10-01 |
| 9 | OdontoApp | Agenda digital [AC] | No evidenciado | Recordatorios [AC]; WhatsApp: No evidenciado | odontoapp.com.ar · 2026-10-01 |
| 10 | Turnito | Duración por servicio, bloqueo de feriados y por inasistencias [AC]; reservas recurrentes solo en Advance/Pro [C] | Reserva sin registro [AC]; cancelación/reprogramación por el paciente dentro de límites [AC]; lista de espera: No evidenciado | **Plan gratis sin WhatsApp ni recordatorios** [C]; 30/100/250 mensajes en planes pagos [C]; mecanismo: No evidenciado | turnito.app/ar/planes · 2026-10-01 |
| 11 | SimpleTurno | Duración por tipo de consulta [AC]; resto No evidenciado | Reserva 24/7 [AC]; cancelación por el paciente y lista de espera: No evidenciado | **Gratis: solo email**; Pro: WhatsApp 60/mes [C]; 24 h antes [C] | simpleturno.com (FAQ) · 2026-10-01 |
| 12 | Neocita | No evidenciado | Reserva web/QR [C]; cancelación por el paciente y lista de espera: No evidenciado | **Manual gratis por enlace** ("sale desde tu WhatsApp"); automático pago; bot de turnos en plan pago [C] | neocita.com/recordatorios · 2026-10-01 |
| 13 | Ulifeon | Multi-consultorio, Google Calendar [AC] | Reserva y pago por link [AC]; cancelación y lista de espera: No evidenciado | **No integra WhatsApp ni Instagram: solo compartir el link** [AC]; recordatorios: No evidenciado | ulifeon.com · 2026-10-01 |
| 14 | Dentalink | Ocupación de sillones, horario por dentista, agenda paralela de sobreturnos [C]; anti-solapamiento: No evidenciado | Reprogramación individual y masiva por la clínica [C]; reserva 24/7 y lista de espera: No evidenciado | **Servicio adicional pago**, mensaje fijo, confirmación/cancelación bidireccional [C]; mecanismo: No evidenciado | ayuda.softwaredentalink.com · 2026-10-01 |
| 15 | AgendaPro | Por profesional y sucursal [C]; resto No evidenciado | Reserva 24/7 por link [AC]; lista de espera: No evidenciado | WhatsApp como add-on pago [C] | agendapro.com/es/planes · 2026-10-01 |
| 16 | Doctocliq | Google Calendar [AC] | Link de agendamiento [C]; chatbot add-on [C] | Cupo 50/100/150 por mes [C]; "Meta Business Partner" [AC] | doctocliq.com/planes-y-precios · 2026-10-01 |
| 17 | Dentidesk | Intervalos 15/30/40 min, bloqueo de feriados [C] | Confirmación/cancelación por email [C] | WhatsApp "próximamente" | dentidesk.com/dentidesk/feature · 2026-10-01 |
| 18 | Odontosys | Confirmación automática [AC] | Reserva por el paciente: No evidenciado | Confirmación WhatsApp/email [AC] | odontosys.com · 2026-10-01 |
| 19 | Clinicorp | Estados en tiempo real [C] | Link público 24/7 [AC]; chatbot Cloudia (Premium) [C] | Recordatorios WhatsApp en Premium [AC] | clinicorp.com/planos · 2026-10-01 |
| 20 | Dentrisoft | Multi-dentista [AC] | Link público: No evidenciado | Recordatorios y confirmación WhatsApp [AC] | dentrisoft.com · 2026-10-01 |
| 21 | DtDental | Gestión de citas [AC] | Formulario de agendamiento [AC] | Confirmación con IA [AC]; WhatsApp solo soporte | dtdental.co · 2026-10-01 |
| 22 | OdontoSoft (PE) | Por especialista, silla y tratamiento [AC] | No evidenciado | WhatsApp para contacto [AC]; email (Cloud) [AC] | odontosoft.me · 2026-10-01 |
| 23 | Odontonet | Búsqueda de hueco libre [AC] | No evidenciado | No evidenciado | informaticadental.com · 2026-10-01 |
| 24 | Open Dental | **ASAP List** filtrable [C] | **Web Sched** (recall, nuevos, existentes, ASAP): link para tomar o rechazar huecos [C] | eReminders y texto [C]; WhatsApp: No evidenciado | opendental.com/manual/asaplist.html · 2026-10-01 |
| 25 | Dentally | Sesiones por profesional [C] | Portal 24/7, **cambio/cancelación por link**, depósitos [C]; **listas de espera con estados** [C] | SMS [C]; WhatsApp: No evidenciado | help.dentally.com · 2026-10-01 |
| 26 | EXACT | Control de slots públicos; "sin doble turno" [AC] | Widget de reserva con depósito [AC] | SMS, recall [AC] | exactdental.com.au · 2026-10-01 |
| 27 | Dentrix | No evidenciado | Reserva online [AC] | Texto bidireccional [AC] | dentrix.com · 2026-10-01 |
| 28 | Curve Dental | Agenda en app móvil [AC] | Reserva y confirmación [AC] | Recordatorios [AC] | curvedental.com · 2026-10-01 |
| 29 | Denticon | "Avanzada" [AC] | Reserva online [AC] | Texto/email; agentes IA de llamadas [AC] | planetdds.com/denticon · 2026-10-01 |
| 30 | tab32 | "Calendario inteligente" [AC] | Reserva 24/7 [AC] | Recordatorios por texto [AC] | tab32.com · 2026-10-01 |
| 31 | Weave | No aplica (depende del sistema de gestión) | Reserva integrada; recepcionista IA [AC] | Texto; "fill gaps" [AC]; WhatsApp: No evidenciado | getweave.com · 2026-10-01 |

### A.3 Clínica, cobros, integraciones y seguridad

| # | Producto | Ficha clínica / odontograma | Cobros, facturación, Mercado Pago, obras sociales | Integraciones / API | Seguridad, exportación, trazabilidad | Fuente principal · fecha |
|---|---|---|---|---|---|---|
| 1 | DentalCore | Odontograma por voz, periodontograma, presupuestos versionados [AC]; 17 motores de reglas clínicas [AC] | ARCA y Mercado Pago listados como incluidos [C en /pricing, sin documentación funcional]; 20+ obras sociales [AC]; **seña MP: No evidenciado** | Exportación HL7 FHIR [C como inclusión]; API pública: No evidenciado | **Cita Ley 25.326 y AAIP; no cita Ley 26.529** [C, /privacy]; backups, RBAC, exportación a pedido [C]; auditoría de accesos [AC]; servidores fuera del país (presumible) | dentalcore.app/privacy · 2026-10-01 |
| 2 | Bilog | Odontograma, imágenes, presupuestos [AC]; documentación de presupuestos y laboratorio [C] | Liquidaciones y validaciones de obras sociales [AC + docs]; facturación electrónica [AC]; ARCA y MP: No evidenciado | Asistente IA iAngela [C, changelog]; API: No evidenciado | Ley 25.326, backup, auditoría, exportación: No evidenciado (FAQ vacía) | docs.bilog.com.ar · 2026-10-01 |
| 3 | Naclix | Ficha con formularios; odontograma (solo web) y presupuestos con firma [AC]; periodontograma: No evidenciado | Señas MP, AFIP con CAE y QR, copagos [AC]; liquidación a obras sociales: No evidenciado | Google Calendar bidireccional [AC]; Meta como subprocesador [C] | **Cita Leyes 25.326 y 26.529** [C]; auditoría e historial de versiones [C, privacidad]; **exportación JSON/CSV** [C]; backups [C]; datos en São Paulo y EE. UU. [C] | naclix.com/privacy y /terms · 2026-10-01 |
| 4 | ClinIA | Odontograma 3D, radiografías, presupuestos, receta electrónica [AC] | Cobertura PUCO, facturación AFIP [AC]; MP: No evidenciado | RENAPER, PUCO, HL7 FHIR [AC]; registro ReNaPDiS verificable, no consultado | Backup [AC]; política de privacidad existe [C]; detalle: No evidenciado | clinia.com.ar · 2026-10-01 |
| 5 | Órbita | Odontograma, periodontograma, presupuestos [AC] | Obras sociales, caja, liquidaciones [AC]; ARCA y MP: No evidenciado | Dentalink, Bilog, Benty [AC] | Políticas existen [C]; detalle: No evidenciado | hiorbita.com · 2026-10-01 |
| 6 | Sigo | Historia, odontograma, presupuestos [AC] | Facturación AFIP, cuentas corrientes [AC] | No evidenciado | No evidenciado | sigo.com.ar · 2026-10-01 |
| 7 | OdontoGRAMA | Ficha con imágenes [AC]; odontograma no confirmado | Caja, obras sociales/prepagas [AC] | No evidenciado | Backup en nube [AC] | odontograma.com.ar · 2026-10-01 |
| 8 | OdontoSoft Millennium | Odontograma, periodontograma [AC] | Prepagas/obras sociales [AC]; AFIP: No evidenciado | No evidenciado | Datos locales; genérico [AC] | gbsystems.com/os · 2026-10-01 |
| 9 | OdontoApp | Historia y odontograma [AC] | No evidenciado | No evidenciado | Solo enlace a política de privacidad [C] | odontoapp.com.ar · 2026-10-01 |
| 10 | Turnito | **No odontológico**: sin ficha clínica ni odontograma | **Seña MP comprobada, incluso en el plan gratis** (comisión 5%; 0% en Pro) [C] | Google Calendar/Meet, WordPress, Telegram [AC] | Privacidad cita solo GDPR/AEPD, **no la Ley 25.326** [C]; exportación a planilla [AC]; historial de cambios: No evidenciado | turnito.app/politicas-de-privacidad · 2026-10-01 |
| 11 | SimpleTurno | No aplica (sin historia clínica) | **Seña MP solo en Pro** [C]; facturación: No evidenciado | Google Calendar [AC] | "Podés exportarlos" sin procedimiento [C, términos]; no cita Ley 25.326 [C] | simpleturno.com/terminos · 2026-10-01 |
| 12 | Neocita | **Ficha genérica** ("historia clínica, estudios e imágenes") [AC]; odontograma: No evidenciado | **Seña MP solo en plan pago** [C]; caja [AC]; factura digital (pago) [C] | No evidenciado | No cita Ley 25.326; comparte con "advertising partners" [C]; exportación: No evidenciado | neocita.com/privacidad.php · 2026-10-01 |
| 13 | Ulifeon | No evidenciado (no es software clínico) | Cobro anticipado MP; comisión al paciente [AC] | Google Calendar [AC] | "Cumple Ley 25.326" [AC, política no hallada] | ulifeon.com · 2026-10-01 |
| 14 | Dentalink | Ficha, odontograma, periodontograma, imágenes [AC]; presupuestos en plan Esencial [C] | **Facturación electrónica solo Colombia y México** [C, ayuda]; ARCA y MP: No evidenciado; obras sociales argentinas no verificadas | API sin documentación pública | Ley 25.326/26.529, exportación: No evidenciado | ayuda.softwaredentalink.com · 2026-10-01 |
| 15 | AgendaPro | Fichas con adjuntos [AC]; odontograma: No evidenciado | Pago anticipado [AC]; facturación "próximamente" [C] | API en plan Pro [C] | "Sumamente seguras" [AC] | agendapro.com/es/planes · 2026-10-01 |
| 16 | Doctocliq | Odontograma, periodontograma, presupuestos [C] | Facturación electrónica MX/PE/EC/CO/RD, **no Argentina** [C] | Google Calendar [AC] | No evidenciado | doctocliq.com/planes-y-precios · 2026-10-01 |
| 17 | Dentidesk | Anamnesis, odontograma, imágenes, presupuestos [C] | Convenios, cobranza, morosos [C]; Argentina: No evidenciado | SII, Alegra [AC] | Usuarios y permisos [C] | dentidesk.com/dentidesk/feature · 2026-10-01 |
| 18 | Odontosys | Odontograma, presupuestos [AC] | Planes de pago [AC] | No evidenciado | TLS, AES-256, AWS [AC] | odontosys.com · 2026-10-01 |
| 19 | Clinicorp | Odontograma, presupuestos [C] | NFS-e, PIX, boleto [C]; no aplica a Argentina | Cloudia, cámara intraoral [C] | No evidenciado | clinicorp.com/planos · 2026-10-01 |
| 20 | Dentrisoft | Odontograma, plan y presupuesto [AC] | Cartera, RIPS [AC] | API en Enterprise [AC] | Habeas Data [AC] | dentrisoft.com · 2026-10-01 |
| 21 | DtDental | Odontograma interactivo [AC] | DIAN, RIPS [AC] | No evidenciado | "Cumple normativas" [AC] | dtdental.co · 2026-10-01 |
| 22 | OdontoSoft (PE) | Odontograma; DICOM [AC] | Caja, SUNAT [AC] | SUNAT [AC] | Backup diario (Cloud) [AC] | odontosoft.me · 2026-10-01 |
| 23 | Odontonet | Odontograma 3D [AC] | Caja y facturación [AC] | No evidenciado | Backup [AC] | informaticadental.com · 2026-10-01 |
| 24 | Open Dental | Odontograma 3D [AC]; imágenes incluidas [C] | Seguros EE. UU. [AC] | **API REST pública documentada** [C] | No evidenciado | opendental.com/site/apiimplementation.html · 2026-10-01 |
| 25 | Dentally | Charting con IA [AC] | Depósitos online [C] | Developer Hub [AC] | Roles por nivel [C] | help.dentally.com · 2026-10-01 |
| 26 | EXACT | Pearl AI [AC] | Depósitos con tarjeta [AC] | Pearl AI [AC] | No evidenciado | exactdental.com.au · 2026-10-01 |
| 27 | Dentrix | Imágenes, IA [AC] | Seguros, cobranza [AC] | No evidenciado | Backup gestionado [AC] | dentrix.com · 2026-10-01 |
| 28 | Curve Dental | Charting, perio, IA [AC] | Seguros, Curve Pay [AC] | Partners [AC] | Genérico | curvedental.com · 2026-10-01 |
| 29 | Denticon | Charting por voz [AC] | Ciclo de ingresos [AC] | 25+ integraciones [AC] | SOC 2 Type 2, HIPAA declarados [AC] | planetdds.com/denticon · 2026-10-01 |
| 30 | tab32 | Charting, IA [AC] | Precio por transacción [C] | Migración [AC] | "HIPAA-compliant" [AC] | tab32.com · 2026-10-01 |
| 31 | Weave | No aplica | Text to Pay [AC] | Con sistemas de gestión [AC] | No evidenciado | getweave.com · 2026-10-01 |

---

## B. Matriz de puntuación (0 a 5)

**Pesos:** T = Gestión de turnos y automatización (25%); C = Funcionalidad odontológica clínica (20%); I = Integraciones locales y WhatsApp (15%); A = Administración, cobros y facturación (15%); P = Experiencia del paciente (10%); S = Seguridad, exportación y trazabilidad (10%); $ = Precio y facilidad de adopción (5%).

**Total ponderado** = (T×25 + C×20 + I×15 + A×15 + P×10 + S×10 + $×5) / 100. Los totales se calcularon con un script a partir de las notas de la tabla, no a mano.

| Rank | Sistema | T | C | I | A | P | S | $ | **Total** | Confianza |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Naclix (AR) | 4 | 3 | 4 | 4 | 3 | 4 | 5 | **3,75** | Medio |
| 2 | DentalCore (AR) | 3 | 4 | 4 | 4 | 3 | 4 | 4 | **3,65** | Medio |
| 3 | Bilog (AR) | 3 | 4 | 3 | 4 | 3 | 1\* | 3 | **3,15** | Medio |
| 3 | ClinIA (AR) | 3 | 4 | 4 | 3 | 3 | 2 | 1\* | **3,15** | Bajo |
| 5 | Órbita (AR) | 4 | 3 | 3 | 3 | 3 | 1\* | 2 | **3,00** | Bajo |
| 6 | Doctocliq (PE, inferido) | 4 | 4 | 2 | 2 | 3 | 0\* | 5 | **2,95** | Medio |
| 7 | Dentalink (CL) | 4 | 4 | 2 | 2 | 3 | 1\* | 2 | **2,90** | Medio |
| 7 | Clinicorp (BR) | 4 | 3 | 2 | 3 | 4 | 0\* | 3 | **2,90** | Medio |
| 9 | Denticon (US) | 3 | 3 | 1 | 3 | 3 | 3 | 1\* | **2,60** | Bajo |
| 10 | Open Dental (US) | 4 | 2 | 1 | 2 | 4 | 1\* | 4 | **2,55** | Alto |
| 11 | Dentally (UK) | 4 | 2 | 1 | 2 | 4 | 2 | 1\* | **2,50** | Medio |
| 11 | tab32 (US) | 3 | 3 | 0\* | 3 | 3 | 2 | 4 | **2,50** | Bajo |
| 13 | Dentrisoft (CO) | 3 | 3 | 2 | 2 | 1\* | 2 | 4 | **2,45** | Bajo |
| 13 | Curve Dental (US) | 3 | 4 | 0\* | 3 | 3 | 1\* | 1\* | **2,45** | Bajo |
| 15 | Neocita (AR) | 3 | 1 | 3 | 3 | 2 | 1 | 5 | **2,40** | Medio |
| 16 | AgendaPro (CL) | 3 | 1\* | 2 | 2 | 4 | 1\* | 5 | **2,30** | Medio |
| 17 | Turnito (AR/LatAm) | 3 | 0\* | 3 | 2 | 4 | 1 | 5 | **2,25** | Medio |
| 18 | Sigo (AR) | 2 | 3 | 2 | 3 | 1\* | 0\* | 4 | **2,15** | Bajo |
| 18 | Dentidesk (CL) | 2 | 4 | 0\* | 3 | 2 | 1\* | 2 | **2,15** | Medio |
| 18 | Dentrix (US) | 3 | 2 | 0\* | 3 | 3 | 2 | 1\* | **2,15** | Bajo |
| 18 | SimpleTurno (AR) | 3 | 0\* | 3 | 2 | 3 | 1 | 5 | **2,15** | Medio |
| 22 | Odontosys (UY) | 2 | 2 | 2 | 2 | 1\* | 3 | 1\* | **1,95** | Bajo |
| 22 | OdontoSoft (PE) | 2 | 3 | 1\* | 2 | 0\* | 2 | 4 | **1,95** | Bajo |
| 24 | OdontoSoft Millennium (AR) | 2 | 3 | 1\* | 2 | 0\* | 1\* | 3 | **1,80** | Bajo |
| 24 | EXACT (UK/AU) | 4 | 1\* | 0\* | 1\* | 4 | 0\* | 1\* | **1,80** | Bajo |
| 24 | Ulifeon (AR) | 2 | 0\* | 2 | 2 | 3 | 2 | 4 | **1,80** | Bajo |
| 27 | Weave (US) | 3 | 0\* | 0\* | 3 | 4 | 0\* | 1\* | **1,65** | Bajo |
| 28 | OdontoGRAMA (AR) | 1\* | 2 | 1\* | 3 | 0\* | 2 | 3 | **1,60** | Bajo |
| 29 | DtDental (CO) | 2 | 2 | 0\* | 2 | 2 | 1\* | 1\* | **1,55** | Bajo |
| 30 | Odontonet (ES) | 1\* | 3 | 0\* | 2 | 0\* | 2 | 0\* | **1,35** | Bajo |
| 31 | OdontoApp (AR) | 1 | 2 | 0\* | 0\* | 0\* | 0\* | 1 | **0,70** | Bajo |

### Nota metodológica

- **Escala.** 0 = no evidenciado o no aplica; 1 = mención mínima o genérica; 2 = cobertura parcial; 3 = cobertura razonable declarada; 4 = cobertura amplia declarada o parcialmente comprobada; 5 = cobertura amplia y comprobada [C].
- **Tope por afirmación comercial.** Si un criterio se sostiene solo en [AC], la nota máxima es 4. El 5 exige [C].
- **"No evidenciado".** Puntúa bajo (0 o 1) y se marca con **\***. Penaliza la falta de evidencia pública, no la ausencia real de la función.
- **Criterio I** (integraciones locales y WhatsApp). Mide lo aplicable a Argentina: WhatsApp, ARCA/AFIP, Mercado Pago, obras sociales y PUCO. Una API genérica sin integraciones locales suma como máximo 1.
- **Criterio S.** Valora que una política de privacidad cite la normativa argentina, la exportación y la auditoría documentadas. A Naclix se le asignó 4 y no 5, pese a su documentación [C], porque aloja datos de salud fuera del país y depende de un proveedor unipersonal.
- **Confianza por sistema.** Alto = documentación técnica o manual; Medio = varias páginas oficiales con partes [C] (precios, ayuda, privacidad); Bajo = una sola página o casi todo [AC].

### Lectura crítica

1. **El ranking mide evidencia pública, no calidad.** Ningún sistema argentino tiene confianza alta. El liderazgo de Naclix (3,75) y DentalCore (3,65) se apoya en amplitud declarada, con comprobación limitada a precios, privacidad y términos.
2. **La segunda pasada movió el orden.** DentalCore bajó en T: sus funciones de agenda no están evidenciadas y no hay prueba gratuita. Bilog subió en C y P por su documentación [C], pero no en T (recordatorios manuales). Dentalink bajó en A (sin facturación en Argentina). Turnito y SimpleTurno subieron en $ y P por sus planes comprobados.
3. Las diferencias menores a 0,2 puntos (puestos 3 a 8) no son concluyentes: deben desempatarse en las demos.

---

## C. Análisis competitivo

### C.1 Funcionalidades estándar del mercado (paridad mínima)

- **Agenda multiprofesional**, a menudo por sillón (Bilog, ClinIA, Órbita, Dentalink [C]).
- **Recordatorios por WhatsApp o email.** WhatsApp está presente en casi todos los sistemas latinoamericanos, pero con mecanismos heterogéneos y sin evidencia de la API oficial (ver C.3).
- **Reserva online por link** en el segmento nube (Bilog [C], Doctocliq [C], Naclix, DentalCore, ClinIA, Clinicorp, Turnito, SimpleTurno, Neocita [C], Ulifeon).
- **Historia clínica con odontograma y presupuestos** en los sistemas odontológicos (casi siempre [AC]; [C] en Doctocliq, Dentidesk, Clinicorp y Dentalink para presupuestos).
- **Seña o cobro anticipado con Mercado Pago** en las agendas argentinas: Turnito [C, incluso gratis], SimpleTurno Pro [C], Neocita en plan pago [C], Ulifeon [AC], Naclix [AC].
- **Plan gratuito o freemium** en el segmento chico: Turnito, SimpleTurno, Neocita, Naclix, Bilog, Doctocliq, Ulifeon, OdontoGRAMA. No es un diferencial.

### C.2 Diferenciadores reales

**Comprobados [C]:**

| Diferenciador | Quién | Fuente |
|---|---|---|
| Lista ASAP + reserva por link para tomar o rechazar huecos | Open Dental | Manual y Web Sched |
| Listas de espera con estados; portal con depósito y cambio/cancelación por link | Dentally | Centro de ayuda y artículo oficial |
| Agenda paralela de sobreturnos, ocupación de sillones, reprogramación masiva | Dentalink | Página de agenda |
| Confirmación bidireccional que cambia el estado del turno | Dentalink (adicional pago), Bilog (por palabra clave) | Centros de ayuda |
| Exportación JSON/CSV, auditoría con historial de versiones, política que cita las Leyes 25.326 y 26.529 | Naclix | Términos y privacidad |
| Política de privacidad que cita la Ley 25.326 y la AAIP | DentalCore | /privacy |
| Precio publicado y cupos de WhatsApp explícitos por plan | Naclix (ARS), Turnito (ARS), SimpleTurno (ARS), Neocita (ARS), Doctocliq, AgendaPro | Páginas de precios |
| API REST pública documentada | Open Dental | Documentación de API |

**Solo afirmación comercial [AC]** (a verificar en demo):

| Diferenciador declarado | Quién |
|---|---|
| Lista de espera con aviso automático; sobreturnos; WhatsApp "canal oficial" | Naclix |
| Bot que ofrece los huecos cancelados; ARCA + obras sociales + Mercado Pago en un plan único; reglas clínicas | DentalCore |
| Anti-solapamiento por sillón; asistente IA que agenda por WhatsApp | Órbita |
| PUCO, RENAPER, receta electrónica HL7 FHIR | ClinIA |
| Liquidación y validación de obras sociales | Bilog |
| Cancelación y reprogramación por el paciente dentro de límites | Turnito, ClinIA, Clinicorp |

### C.3 Vacíos frecuentes en el mercado argentino

1. **WhatsApp sin API oficial documentada.** Ningún competidor documenta el uso de la API oficial de WhatsApp Business. DentalCore la descarta expresamente (sesión por QR, riesgo de bloqueo). Bilog envía en forma manual o semiautomática desde un número autorizado. Neocita usa un enlace en su plan gratuito. Turnito, SimpleTurno y Dentalink no indican el mecanismo. Naclix ("canal oficial") y Doctocliq ("Meta Business Partner") lo sugieren sin documentarlo. **Consecuencia:** un enlace `wa.me` semiautomático está a la par del mercado.
2. **Lista de espera: existe, pero poco documentada.** *Corrección respecto de la versión anterior del informe*, que afirmaba que ningún sistema local tenía lista de espera: **Naclix la declara**, con aviso automático al siguiente paciente [AC], y DentalCore declara ofrecer los huecos cancelados [AC]. El vacío real está en que ningún sistema local la documenta ni muestra su flujo (estados, prioridad, vencimiento de la oferta), como sí hacen Open Dental y Dentally [C].
3. **Reglas finas de agenda.** No se evidencian **horarios recurrentes configurables** con excepciones; lo más cercano es "horario por dentista" en Dentalink [C] y los intervalos y bloqueos de feriados de Dentidesk [C]. La **prevención de solapamientos** solo aparece como [AC] (Órbita; EXACT, no local). La **reprogramación por el paciente** solo está comprobada en Dentally; en el mercado local, Bilog permite cancelar [C] y Turnito declara cancelar y reprogramar [AC]. La **trazabilidad de cambios de turno** solo aparece en Naclix (auditoría [C]).
4. **Seña + clínica en un mismo producto.** Las agendas con seña comprobada (Turnito, SimpleTurno, Neocita) no tienen clínica odontológica. Entre los sistemas clínicos, la seña con Mercado Pago no está evidenciada en DentalCore ni en Bilog; Naclix la declara [AC].
5. **Cumplimiento normativo explícito.** Solo Naclix cita la Ley 26.529 (historia clínica). DentalCore y Naclix citan la Ley 25.326 [C]. Turnito, SimpleTurno y Neocita no la citan [C]; en el resto no está evidenciada. Varios alojan datos de salud fuera del país (Naclix, DentalCore presumiblemente).
6. **Transparencia de precios en los sistemas clínicos.** Bilog, ClinIA, Órbita y Dentalink no publican precios. DentalCore cobra en USD. Naclix y Sigo publican en ARS.
7. **Dependencia de referentes regionales sin adaptación local.** Dentalink no factura en Argentina y su sitio /ar no tiene contenido local [C]. Doctocliq no factura en Argentina [C].

### C.4 Oportunidades de innovación

- **Lista de espera documentada y transparente** que ofrezca huecos liberados por WhatsApp (enlace semiautomático), con estados y orden de prioridad visibles. Toma el patrón de Open Dental y Dentally y lo lleva al canal local.
- **Agenda con reglas explícitas:** horario recurrente con excepciones, duración por prestación y anti-solapamiento por profesional y por sillón, con historial de cada cambio. Hoy nadie lo muestra en el mercado local.
- **Autogestión del paciente** (cancelar y reprogramar dentro de reglas configurables) integrada con la seña de Mercado Pago y la lista de espera.
- **Confianza como diferencial:** política que cite las Leyes 25.326 y 26.529, exportación de datos documentada y precio publicado en ARS.
- **Etapa posterior:** verificación de cobertura (PUCO), facturación ARCA y obras sociales, donde los sistemas clínicos locales ya compiten.

---

## D. Recomendación final

### D.1 Cinco competidores prioritarios para demo

El segmento primario es el **odontólogo independiente**. Se priorizan competidores locales que ese usuario evaluaría, más un referente regional de agenda.

| # | Sistema | Por qué | Qué verificar en la demo |
|---|---|---|---|
| 1 | **Naclix** | Primer puesto (3,75); precio en ARS con plan gratuito; único local que declara lista de espera, sobreturnos y auditoría, y que documenta exportación y la Ley 26.529 | Flujo real de la lista de espera (quién recibe el aviso, cuánto dura la oferta); si WhatsApp usa la API oficial o una sesión vinculada; anti-solapamiento y horarios recurrentes; cancelación por el paciente; odontograma web; emisión AFIP/ARCA con CAE; continuidad del proveedor unipersonal y ubicación de los datos |
| 2 | **DentalCore** | Segundo puesto (3,65); propuesta "todo incluido" para Argentina; WhatsApp por QR declarado | Riesgo de la sesión por QR; cómo el bot ofrece huecos (¿hay lista de espera?); si existe seña con Mercado Pago (hoy No evidenciado); ARCA y obras sociales funcionando; sobreturnos, bloqueos y solapamientos; auditoría de accesos |
| 3 | **Bilog** | Mayor escala local declarada; freemium; documentación pública de agenda y portal | Flujo de recordatorio manual vs. módulo masivo; reserva por link (límite de 15 días en el plan gratis); reglas de cancelación; reprogramación; obras sociales; precios de Lite/Premium; ARCA |
| 4 | **Turnito** | Sustituto real del independiente: agenda barata con seña MP comprobada en el plan gratis | Cancelación y reprogramación por el paciente (hoy [AC]); bloqueos; ausencia de ficha clínica (¿suficiente para un odontólogo?); mecanismo de WhatsApp; tratamiento de datos (solo GDPR) |
| 5 | **Dentalink** | Referente regional con la agenda más comprobada (sobreturnos, sillones, reprogramación masiva, confirmación bidireccional) | Mecanismo y costo del adicional de WhatsApp; anti-solapamiento; qué ofrece realmente en Argentina sin facturación local; precio |

Alternativas: **ClinIA** (integraciones regulatorias argentinas, relevante para la etapa con obras sociales y receta) y **SimpleTurno** o **Neocita** (agendas de bajo costo con seña MP en planes pagos).

### D.2 Tres productos de referencia de experiencia de usuario

1. **Open Dental (Web Sched + ASAP List):** reserva por link y oferta de huecos documentadas [C]. Modelo para la lista de espera.
2. **Dentally (portal + listas de espera):** listas con estados, portal 24/7 con depósito y cambio o cancelación por link [C]. Modelo para la autogestión con seña.
3. **Clinicorp (link público + estados en tiempo real):** autoagendamiento compartible por WhatsApp y estados de turno [C en planes y post oficial]. Es el referente latinoamericano más cercano al canal.

### D.3 MVP sugerido

**Segmento primario:** odontólogo independiente (1 profesional, 1 sillón). El sillón se modela como **recurso** con valor por defecto 1. La regla de solapamiento se aplica **por profesional y por sillón**, de modo que el crecimiento a varios sillones no requiera rediseñar la lógica.

**Imprescindible (v1)**
1. Agenda con **duraciones variables por prestación**, configurables.
2. **Horario recurrente configurable** (días y franjas de atención).
3. **Bloqueos puntuales** (vacaciones, feriados, ausencias).
4. **Prevención de solapamientos** por profesional y por sillón.
5. **Reserva 24/7 por link**, con un flujo definido cuando no hay horarios disponibles (ofrecer la lista de espera).
6. **Recordatorio y confirmación por WhatsApp.** Se prefiere la **WhatsApp Cloud API en modo prueba** (automática, con confirmación por respuesta) si la configuración técnica resulta viable para el prototipo. La alternativa es un enlace `wa.me` semiautomático (el sistema arma el mensaje y el profesional lo envía), que está a la par del mercado según C.3. Con datos ficticios y el número de pruebas de Meta alcanza para la demo; para uso real con pacientes haría falta verificación de empresa, plantillas aprobadas y costo por conversación (sin fuente verificada aún).
7. **Cancelación y reprogramación por el paciente** dentro de las reglas configuradas.
8. **Seña con Mercado Pago** (Checkout Pro).
9. **Trazabilidad de cambios de turno** (quién, cuándo, qué cambió).
10. **Lista de espera.**
11. **Ficha clínica mínima:** datos del paciente, anamnesis y evolución en texto.
12. **Presupuestos simples** y **registro de pago simple**.

**Diferenciador**
- Lista de espera que **ofrece los huecos liberados por WhatsApp** (semiautomática). Hoy solo hay [AC] locales sin flujo documentado.
- **Horario recurrente + trazabilidad** de cada cambio de agenda. No está evidenciado en conjunto en ningún sistema.
- **Precio publicado en ARS**, frente a sistemas clínicos que cotizan a pedido o cobran en USD.

**Etapas posteriores**
- Odontograma completo (v1.1).
- Obras sociales con códigos y valores (v1.1).
- Imágenes y radiografías.
- Facturación electrónica ARCA.
- Caja completa.
- WhatsApp por API oficial **en producción** (verificación de empresa, plantillas y costo por conversación). *A verificar en la documentación de Meta:* Meta crea un número de pruebas al empezar, pero el límite de 5 destinatarios verificados proviene de fuentes de terceros; no se afirman costos sin fuente.
- Sincronización con Google Calendar.
- Multi-profesional y multi-sillón en la interfaz (el modelo de datos ya lo soporta).
- API pública.

### D.4 Reglas de negocio configurables (valores por defecto propuestos)

Son **decisiones de diseño del autor, no hechos de mercado**. Todas son configurables por el profesional.

| Regla | Valor por defecto propuesto |
|---|---|
| Ventana de cancelación sin penalidad | 24 h antes del turno |
| Horizonte máximo de reserva | 60 días |
| Antelación mínima para reservar | Configurable (sin valor de mercado de referencia) |
| Paciente nuevo | Reserva directa, con aprobación del profesional opcional |
| Seña si el paciente cancela fuera de término | Se retiene |
| Seña si cancela el odontólogo | Se devuelve |

**Pregunta abierta:** la retención de la seña podría tener implicancias según la Ley 24.240 de Defensa del Consumidor (por ejemplo, el derecho de revocación o las cláusulas abusivas). Matiz: el artículo 2 de esa ley excluye los servicios de profesionales liberales con título universitario y matrícula (su publicidad sí queda alcanzada), de modo que en la relación paciente–odontólogo podría no aplicar; el análisis puede cambiar si el cliente es una clínica (persona jurídica) o se evalúa la relación con el proveedor del software. Este informe no da asesoría legal; el punto queda para consulta profesional antes de definir la regla definitiva.

---

## Limitaciones del estudio

- **Herramienta.** Las notas se obtuvieron con WebFetch, que devuelve **resúmenes automáticos** y no el texto literal (salvo citas entrecomilladas). Puede haber omisiones o simplificaciones.
- **Tipo de fuente.** Se leyeron **mayormente páginas comerciales**. Los centros de ayuda y las políticas de privacidad solo se leyeron para los sistemas de la segunda pasada (DentalCore, Bilog, Dentalink, Turnito, SimpleTurno, Naclix, Neocita) y para Open Dental y Dentally.
- **Fuentes sin leer.** No se leyeron: la política de privacidad de Dentalink y la de Ulifeon (no hallada); la ficha de Google Play de Bilog, Neocita y Naclix; las páginas de precios de Órbita y Curve Dental; el registro ReNaPDiS (ClinIA); la especificación completa de la API de Open Dental; las FAQ de DentalCore (acordeones no legibles); payments.bilog.com.ar.
- **Sin demos ni pruebas.** La matriz B es una estimación preliminar basada en evidencia pública.
- **Sesgo de fuentes.** Las comparativas de Naclix, Doctocliq, Turnito y DentalCore son contenido de competidores interesados. Las cifras de adopción son, salvo excepción, publicadas por el propio proveedor.
- **Notas sobrescritas.** Las notas `dentalink.md` y `dentidesk.md` fueron sobrescritas en la primera pasada por otro relevamiento (formato y fuentes distintos). Se usa la versión vigente; la anterior no puede reconstruirse.
- **Contradicciones menores sin resolver.** Prueba de Dentidesk (15 días según el sitio, 30 según terceros). Data safety de Neocita en Google Play frente a su política web.

---

## Verificación de fuentes

> **Estado: pendiente.** Esta sección no está completa: la consigna exige que el autor abra y compruebe personalmente al menos 5 fuentes de tipos distintos. Las columnas "Qué encontró el autor" y "Qué corrigió" quedan para completar tras esa comprobación.

### Plantilla de verificación

| # | Fuente y tipo | Qué afirma el informe | Qué encontró el autor | Qué corrigió |
|---|---|---|---|---|
| 1 | [Elegir de las candidatas] | [Afirmación del informe] | [A completar por el autor] | [A completar por el autor] |
| 2 | [Elegir de las candidatas] | [Afirmación del informe] | [A completar por el autor] | [A completar por el autor] |
| 3 | [Elegir de las candidatas] | [Afirmación del informe] | [A completar por el autor] | [A completar por el autor] |
| 4 | [Elegir de las candidatas] | [Afirmación del informe] | [A completar por el autor] | [A completar por el autor] |
| 5 | [Elegir de las candidatas] | [Afirmación del informe] | [A completar por el autor] | [A completar por el autor] |

### Fuentes candidatas (8, de tipos distintos)

| # | Tipo | URL | Afirmación concreta a comprobar | Qué encontró el autor | Qué corrigió |
|---|---|---|---|---|---|
| 1 | Sitio oficial | https://naclix.com/ | Naclix declara lista de espera con aviso automático al siguiente paciente y sobreturnos marcados | [A completar por el autor] | [A completar por el autor] |
| 2 | Página de precios | https://dentalcore.app/pricing | USD 50/mes con 2 usuarios, USD 10 por usuario adicional; garantía de reembolso de 14 días (no prueba gratuita) | [A completar por el autor] | [A completar por el autor] |
| 3 | Centro de ayuda | https://docs.bilog.com.ar/schedule/reminders | El recordatorio por WhatsApp de Bilog "no se puede programar para que se envíe por sí sola"; el masivo requiere un módulo adicional | [A completar por el autor] | [A completar por el autor] |
| 4 | Política de privacidad | https://dentalcore.app/privacy | Cita la Ley 25.326 y la AAIP, y no cita la Ley 26.529 | [A completar por el autor] | [A completar por el autor] |
| 5 | Ficha de app | https://apps.apple.com/us/app/bilog-gesti%C3%B3n-odontol%C3%B3gica/id1554140449 | Existe app iOS nativa "Bilog Gestión Odontológica" (v7.21.1, iOS 15.5+, gratuita) | [A completar por el autor] | [A completar por el autor] |
| 6 | Documentación técnica | https://opendental.com/site/apiimplementation.html | API REST con Developer Key + Customer Key y límites de tasa | [A completar por el autor] | [A completar por el autor] |
| 7 | Reseña de tercero | https://www.capterra.com/p/196361/Dentalink/ | Dentalink tiene 2 reseñas con 5,0 y precio de USD 29/usuario/mes (moneda inferida) | [A completar por el autor] | [A completar por el autor] |
| 8 | Estudio académico | https://ideas.repec.org/a/cwf/dentar/dent2025127.html | 68% de historia clínica en papel y 66% sin software de diagnóstico y diseño de tratamientos (n=100, CABA/GBA, 2024) | [A completar por el autor] | [A completar por el autor] |

Fuentes adicionales útiles: ayuda de Dentalink sobre servicios adicionales (https://ayuda.softwaredentalink.com/es/articles/9488169-servicios-adicionales): facturación electrónica solo en Colombia y México. Planes de Turnito (https://turnito.app/ar/planes/): sin WhatsApp en el plan gratis.

### Hallazgos de la verificación asistida por el agente

En la segunda pasada, el agente releyó fuentes oficiales y corrigió las siguientes afirmaciones de la primera versión. **Son antecedentes y no sustituyen la comprobación personal** que exige la consigna.

1. **DentalCore:** la "prueba de 14 días" es una garantía de reembolso. WhatsApp funciona por sesión con QR, no por API oficial. El precio de USD 50/mes está comprobado en /pricing. La política cita la Ley 25.326, no la 26.529.
2. **Dentalink:** la facturación electrónica solo está disponible en Colombia y México según su ayuda. WhatsApp es un servicio adicional pago. No hay evidencia de ARCA ni de datos locales en /ar; se reclasificó como referente regional, no local.
3. **Bilog:** los recordatorios por WhatsApp son manuales o semiautomáticos (no se programan solos). Tiene plan freemium más Lite y Premium sin precio. La app iOS está comprobada.
4. **Naclix** (nuevo): sí evidencia lista de espera y sobreturnos [AC], auditoría y exportación JSON/CSV [C] y precios en ARS. Es multirrubro. Se corrigió el vacío "ningún sistema local tiene lista de espera".
5. **Turnito:** el plan gratis no incluye WhatsApp. La seña con Mercado Pago está confirmada (comisión del 5% en el plan gratis). La cifra de "40.000 usuarios" no se verificó. Es una agenda multirrubro, no odontológica.
6. **SimpleTurno:** el plan gratis solo envía recordatorios por email; WhatsApp y la seña con Mercado Pago están en Pro.
7. **Neocita** (nuevo): recordatorios manuales gratis por enlace y automáticos pagos. Seña con Mercado Pago solo en el plan pago. Solo app Android. Ficha genérica.
8. **Ulifeon** (nuevo): gratis para el profesional; el paciente paga 2,2% + IVA. No integra WhatsApp ni Instagram: solo permite compartir el link.
9. **Transversal:** ningún competidor documenta la API oficial de WhatsApp Business, por lo que un enlace `wa.me` está a la par del mercado.

---

## Referencias

Todas las fuentes se consultaron el **2026-10-01**. "(no leída)" indica una URL referida por un buscador que no se leyó directamente.

| Sistema | Fuentes |
|---|---|
| Naclix | https://naclix.com/ ; https://naclix.com/privacy ; https://naclix.com/terms ; https://naclix.com/comparar/dentalink ; https://app.naclix.com/ ; https://apps.apple.com/ar/app/naclix/id6756287334 |
| DentalCore | https://dentalcore.app/ ; https://dentalcore.app/pricing ; https://dentalcore.app/privacy ; https://dentalcore.app/terms ; https://dentalcore.app/blog/benchmark-software-dental-latinoamerica-2026 ; /faq (no legible) |
| Bilog | https://bilog.com.ar/ ; https://bilog.com.ar/planes ; https://docs.bilog.com.ar/schedule/reminders ; https://docs.bilog.com.ar/schedule/online-appointment ; https://docs.bilog.com.ar/schedule/app-appointment ; https://docs.bilog.com.ar/schedule/appointments ; https://apps.apple.com/us/app/bilog-gesti%C3%B3n-odontol%C3%B3gica/id1554140449 |
| ClinIA | https://www.clinia.com.ar/odontologia ; (no leída) https://www.argentina.gob.ar/salud/digital/renapdis/receta-electronica/plataformas |
| Órbita | https://hiorbita.com/ |
| Sigo | https://sigo.com.ar/ |
| OdontoGRAMA | https://odontograma.com.ar/ |
| OdontoSoft Millennium | https://gbsystems.com/os/ ; https://gbsystems.com/os/promo.htm |
| OdontoApp | https://odontoapp.com.ar/ |
| Turnito | https://turnito.app/ ; https://turnito.app/ar/planes/ ; https://turnito.app/funcionalidades/ ; https://turnito.app/politicas-de-privacidad/ ; https://turnito.app/terminos-y-condiciones/ ; https://turnito.app/novedades/ ; https://turnito.app/blog/las-mejores-apps-de-turnos-para-odontologos-en-argentina-2026/ |
| SimpleTurno | https://simpleturno.com/rubros/odontologia ; https://simpleturno.com/ (FAQ, #precios) ; https://simpleturno.com/privacy ; https://simpleturno.com/terminos |
| Neocita | https://www.neocita.com/ ; https://www.neocita.com/precios.php ; https://www.neocita.com/recordatorios-turnos-whatsapp.php ; https://www.neocita.com/bot-turnos-whatsapp.php ; https://www.neocita.com/contacto.php ; https://www.neocita.com/privacidad.php ; https://play.google.com/store/apps/datasafety?id=com.neocita.neocita&hl=es |
| Ulifeon | https://ulifeon.com/ ; https://apps.apple.com/ar/app/ulifeon/id1670503914 ; (solo resultado de búsqueda) colodontcba.org.ar/novedades/ |
| Dentalink | https://www.softwaredentalink.com/ ; https://www.softwaredentalink.com/experiencia-de-pacientes/agenda ; https://www.softwaredentalink.com/planes ; https://www.softwaredentalink.com/ar/ ; https://ayuda.softwaredentalink.com/es/articles/9493201-notificaciones-automaticas-por-whatsapp ; https://ayuda.softwaredentalink.com/es/articles/9488169-servicios-adicionales ; https://www.capterra.com/p/196361/Dentalink/ |
| AgendaPro | https://agendapro.com/es/dental/software-odontologico ; https://agendapro.com/es/planes ; https://agendapro.com/ar/dental/software-odontologico |
| Doctocliq | https://www.doctocliq.com/ ; https://www.doctocliq.com/planes-y-precios ; https://www.doctocliq.com/mejor-software-dental |
| Dentidesk | https://www.dentidesk.com/ ; https://www.dentidesk.com/dentidesk/feature ; terceros: https://www.doctocliq.com/mejor-software-dental , https://turnito.app/blog/los-mejores-software-de-turnos-para-odontologos-en-chile-2026/ ; (no leída) https://app.dentidesk.com/terminos.php |
| Odontosys | https://odontosys.com/ |
| Clinicorp | https://www.clinicorp.com/planos ; https://www.clinicorp.com/post/agendamento-paciente-online ; terceros: https://www.codental.com.br/blog/melhores-softwares-odontologicos/ |
| Dentrisoft | https://dentrisoft.com/ |
| DtDental | https://dtdental.co/ ; (no leída) https://dtdental.co/2024/10/26/como-funciona-el-software-dental-para-consultorios/ |
| OdontoSoft (Perú) | https://odontosoft.me/ ; (no leída) https://odontosoft.me/blog/cuanto-cuesta-software-dental-peru/ |
| Odontonet | https://informaticadental.com/odontonet/ |
| Open Dental | https://www.opendental.com/ ; https://opendental.com/site/order.html ; https://www.opendental.com/site/websched.html ; https://www.opendental.com/manual/asaplist.html ; https://opendental.com/site/apiimplementation.html ; (no leídas) https://www.opendental.com/site/apispecification.html , https://www.opendental.com/resources/OpenDentalAPI.pdf |
| Dentally | https://www.dentally.com/en-gb/ ; https://www.dentally.com/en-gb/insights-hub/online-appointment-booking ; https://help.dentally.com/en/articles/3621351-how-to-use-waiting-lists ; (no leídas) https://help.dentally.com/en/articles/11331038-how-appointment-slots-are-held-during-online-booking-with-portal , https://www.dentally.com/en-gb/insights-hub/the-appointment-book |
| EXACT | https://www.exactdental.com.au/solutions/patient-experience/online-booking ; https://www.henryscheinone.com/products/exact/ |
| Dentrix | https://www.dentrix.com/ (/products/dentrix-ascend devolvió 404) |
| Curve Dental | https://www.curvedental.com/ |
| Denticon | https://www.planetdds.com/denticon/ |
| tab32 | http://tab32.com/ |
| Weave | https://www.getweave.com/ |
| Contexto de mercado | https://la.dental-tribune.com/news/jornada-de-actualizacion-en-odontologia-2/ ; https://www.uncuyo.edu.ar/prensa/la-nacion-los-odontologos-se-ven-enfrentados-a-una-compleja-realidad-laboral ; https://ideas.repec.org/a/cwf/dentar/dent2025127.html ; https://rentechdigital.com/smartscraper/ru/business-report-details/list-of-dental-clinics-in-argentina ; https://www.ambito.com/informacion-general/dia-del-odontologo-argentina-es-uno-los-paises-mayor-proporcion-dentistas-el-mundo-segun-la-oms-n6197981 |
