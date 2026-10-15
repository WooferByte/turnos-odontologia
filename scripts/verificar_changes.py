#!/usr/bin/env python3
"""Verificación cruzada de CHANGES.md contra knowledge-base/ (solo lectura).

Cómo correrlo, desde la raíz del repositorio:

    backend/.venv/Scripts/python.exe scripts/verificar_changes.py          # Windows
    python3 scripts/verificar_changes.py                                   # cualquier otro caso
    python3 scripts/verificar_changes.py RUTA_A_OTRA_RAIZ                  # raíz con CHANGES.md y knowledge-base/

Solo usa la biblioteca estándar y no escribe nada. Imprime, por cada fila de la
tabla de «Verificación cruzada» de CHANGES.md (1, 2, 3a, 3b, 3c, 4 a 12), los
elementos revisados y las diferencias, o «sin diferencias». Sale con código 1 si
hay alguna diferencia (y con 2 si falta algún archivo de entrada).

Qué cuenta como «citado» (vale para todas las filas):

* Se lee todo CHANGES.md MENOS su propia sección «## Verificación cruzada»: esa
  sección habla de decisiones y reglas pero no es una entrada del índice, y
  contarla haría que el resultado dependiera de su propio texto.
* Un ID se cita cuando aparece como token literal. Un rango como «D195 a D203»
  o «E1..E12» cita SOLO sus dos extremos, no los del medio (la KB ya dice
  «D195 a D203» como etiqueta de un grupo, no como lista de decisiones).
* Un token no cuenta si lo precede una letra, un dígito o un guion (así «P-03»
  no se confunde con el de «RN-RP-03» ni «D1» con «DD-01»).
* Fila 6: una cita es cada token CA-n (con sufijo opcional: CA-2b) y su historia
  es la última «US-NNN» que aparece antes en la MISMA línea (en el mapeo es la
  primera celda). «CA-a+CA-b» son dos citas. «CA-7 a CA-10» cita TODOS los del
  medio (CA-7, CA-8, CA-9 y CA-10; es la única forma en que cierran las 260
  citas de la corrida del 2026-10-14). Cada cita debe existir en 06 tal cual
  (CA-2b es su propio criterio de 06). «Criterio» = par (historia, número)
  distinto, y CA-2b se agrupa con CA-2 (la letra es una variante; así cierran
  los 165 pares). Una CA sin US en su línea es una diferencia.
* Fila 7: D-NN «figura en el registro» si está en la primera celda (la columna
  «Tema») de una fila de tabla bajo un encabezado «### Decisiones del autor»
  de 10_preguntas_abiertas.md; SU-NN si es un «### SU-NN» de 09; P-NN si es la
  primera celda de una fila de 10.
* Fila 9: una referencia es cada elemento de «Leer antes» que apunta a la KB:
  el archivo (1), cada RN/DD/SU/D/E/US citado (los rangos de D, dos extremos),
  cada «sección entre comillas angulares» (en cualquier punto del archivo,
  sin distinguir mayúsculas ni formato), cada «§Palabra» (debe ser un
  encabezado), cada «Flujo N» (encabezado de 07) y cada «fila X» (primera
  celda de una tabla). Los IDs deben aparecer en el archivo que indica la
  entrada. Los CA se cuentan en la fila 6, no acá; el texto libre entre
  paréntesis («pasos 1 y 2») no es una referencia. Se cuentan las apariciones,
  no las distintas.
* Fila 10: las puertas «nombran» un change si su código «C-NN» figura en el
  bloque de «Paralelismo por fase»; donde aparece pegado a un nombre
  compuesto («C-06 sesion-con-jwt») ese nombre debe ser el de la entrada.
  El árbol: padre = el nodo con menos sangría que lo precede; dependencias del
  árbol = ese padre más los códigos entre paréntesis; deben ser iguales a «Depende de».
* Fila 12: «líneas por entrada» = desde el encabezado «### [C-NN]» hasta la
  última línea no vacía de la entrada, encabezado incluido.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

# --------------------------------------------------------------------------
# Lectura
# --------------------------------------------------------------------------

NO_PRECEDIDO = r"(?<![A-Za-z0-9-])"


def leer_entrada():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    raiz = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    archivos = {"CHANGES": raiz / "CHANGES.md"}
    kb = raiz / "knowledge-base"
    for prefijo in ("02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "01"):
        hallados = sorted(kb.glob(f"{prefijo}_*.md"))
        if hallados:
            archivos[prefijo] = hallados[0]
    faltan = [str(p) for p in archivos.values() if not p.is_file()]
    if faltan or not all(k in archivos for k in ("02", "03", "04", "05", "06", "07", "09", "10")):
        print("Faltan archivos de entrada en", raiz, faltan)
        sys.exit(2)
    textos = {k: p.read_text(encoding="utf-8") for k, p in archivos.items()}
    return raiz, textos


RAIZ, TEXTOS = leer_entrada()
CH_COMPLETO = TEXTOS["CHANGES"]
_i = CH_COMPLETO.find("## Verificación cruzada")
CH = CH_COMPLETO[:_i] if _i >= 0 else CH_COMPLETO  # sin la sección de verificación
KB = {k: v for k, v in TEXTOS.items() if k != "CHANGES"}
NOMBRES_KB = {p.name: k for k in KB for p in [next((RAIZ / "knowledge-base").glob(f"{k}_*.md"))]}


def norm(s):
    """Minúsculas, sin backticks ni asteriscos, espacios colapsados."""
    return re.sub(r"\s+", " ", s.replace("`", "").replace("*", "")).strip().casefold()


# --------------------------------------------------------------------------
# Entradas de CHANGES.md
# --------------------------------------------------------------------------

ENC = re.compile(r"^### \[C-(\d+)\] `([^`]*)`[ \t]*$", re.M)


class Entrada:
    pass


def parsear_entradas():
    marcas = list(ENC.finditer(CH))
    entradas = []
    for m in marcas:
        fin = re.compile(r"^(?:### |## |---[ \t]*$)", re.M).search(CH, m.end())
        texto = CH[m.start():fin.start() if fin else len(CH)].rstrip()
        e = Entrada()
        e.num = int(m.group(1))
        e.cod = f"C-{e.num:02d}"
        e.nombre = m.group(2)
        e.texto = texto
        e.lineas = texto.split("\n")
        mo = re.search(r"\*\*Orden\*\*: (\d+)", texto)
        e.orden = int(mo.group(1)) if mo else None
        mo = re.search(r"^- \*\*Objetivo\*\*(?: \(([^)]*)\))?", texto, re.M)
        e.historias = re.findall(r"US-\d{3}", mo.group(1)) if mo and mo.group(1) else []
        mo = re.search(r"^- \*\*Depende de\*\*: (.*)$", texto, re.M)
        e.deps_texto = mo.group(1).strip() if mo else None
        e.deps = re.findall(r"C-\d+", e.deps_texto) if e.deps_texto else []
        mo = re.search(r"^- \*\*Escenarios mínimos\*\*: (.*)$", texto, re.M)
        e.escenarios = mo.group(1) if mo else None
        e.leer = []
        activo = False
        for ln in e.lineas:
            if ln.startswith("- **Leer antes**"):
                activo = True
                continue
            if activo:
                if ln.startswith("  - "):
                    e.leer.append(ln)
                elif ln.strip():
                    activo = False
        entradas.append(e)
    return entradas


ENTRADAS = parsear_entradas()
POR_COD = {e.cod: e for e in ENTRADAS}

# --------------------------------------------------------------------------
# Utilidades de la KB
# --------------------------------------------------------------------------

METODOS = r"(?:GET|POST|PUT|PATCH|DELETE)"
RUTA = re.compile(r"(?<![A-Za-z/])(" + METODOS + r"(?:/" + METODOS + r")*) (/[^\s`,;)(]*)")


def expandir_ruta(m):
    metodos = m.group(1).split("/")
    camino = m.group(2).split("?")[0].rstrip(".")
    alternativas = [camino]
    g = re.search(r"\{([^{}|]*\|[^{}]*)\}", camino)
    if g:
        alternativas = [camino[:g.start()] + o + camino[g.end():] for o in g.group(1).split("|")]
    return [f"{met} {alt}" for met in metodos for alt in alternativas]


def rutas_de(texto):
    """[(ruta, segmento_posterior)] con el texto hasta la próxima ruta de la misma línea."""
    salida = []
    for linea in texto.split("\n"):
        ms = list(RUTA.finditer(linea))
        for k, m in enumerate(ms):
            fin = ms[k + 1].start() if k + 1 < len(ms) else len(linea)
            for r in expandir_ruta(m):
                salida.append((r, linea[m.end():fin]))
    return salida


def secciones_us(texto_06):
    """{US-NNN: texto de su sección} para las historias de la v1 (antes de «Épicas posteriores»)."""
    corte = texto_06.find("## Épicas posteriores")
    v1 = texto_06[:corte] if corte >= 0 else texto_06
    partes = re.split(r"^(?=### US-\d{3} )", v1, flags=re.M)
    res = {}
    for p in partes:
        m = re.match(r"### (US-\d{3}) ", p)
        if m:
            res[m.group(1)] = re.split(r"^## ", p, flags=re.M)[0]
    return res


def dividir_tabla(texto, encabezado):
    """Filas de la primera tabla que sigue a `encabezado` (línea que lo contiene)."""
    i = texto.find(encabezado)
    filas = []
    if i < 0:
        return filas
    for ln in texto[i:].split("\n")[1:]:
        if ln.startswith("|"):
            filas.append([c.strip() for c in ln.strip().strip("|").split("|")])
        elif filas and not ln.strip().startswith("|"):
            break
    return filas


# --------------------------------------------------------------------------
# Las doce filas. Cada una devuelve (elementos_revisados, [diferencias]).
# --------------------------------------------------------------------------

def fila_1():
    dif = []
    n = 0
    for e in ENTRADAS:
        if e.deps_texto is None:
            dif.append(f"{e.cod}: no tiene línea «Depende de»")
            continue
        if not e.deps and not e.deps_texto.lower().startswith("ninguna"):
            dif.append(f"{e.cod}: «Depende de» no es «ninguna» ni una lista de changes: {e.deps_texto!r}")
        for d in e.deps:
            n += 1
            if d == e.cod:
                dif.append(f"{e.cod}: depende de sí mismo")
            elif d not in POR_COD:
                dif.append(f"{e.cod}: depende de {d}, que no existe en este archivo")
            elif POR_COD[d].orden > e.orden:
                dif.append(f"{e.cod} (orden {e.orden}) depende de {d} (orden posterior {POR_COD[d].orden})")
    # sin ciclos
    estado = {}

    def visita(c, pila):
        if estado.get(c) == 2:
            return
        if estado.get(c) == 1:
            dif.append("ciclo de dependencias: " + " -> ".join(pila + [c]))
            return
        estado[c] = 1
        for d in POR_COD[c].deps:
            if d in POR_COD:
                visita(d, pila + [c])
        estado[c] = 2

    for e in ENTRADAS:
        visita(e.cod, [])
    return f"{n} dependencias en {len(ENTRADAS)} changes", dif


def mapeo_historias():
    """{US: (titular_texto, otros_texto)} desde «Mapeo historia → change»; filas repetidas se listan."""
    filas = dividir_tabla(CH, "### Mapeo historia → change")
    res = defaultdict(list)
    for f in filas:
        if f and re.fullmatch(r"US-\d{3}", f[0]) and len(f) >= 3:
            res[f[0]].append(f)
    return res


def fila_2():
    dif = []
    sec = secciones_us(KB["06"])
    mapeo = mapeo_historias()
    implementa = defaultdict(set)  # change -> historias que implementa según el mapeo
    for us in sec:
        filas = mapeo.get(us, [])
        if len(filas) != 1:
            dif.append(f"{us}: tiene {len(filas)} filas en el mapeo (debe ser exactamente 1)")
            continue
        f = filas[0]
        tit = re.findall(r"C-\d+", f[1])
        if len(tit) != 1 or tit[0] not in POR_COD:
            dif.append(f"{us}: change titular inválido {f[1]!r}")
            continue
        implementa[tit[0]].add(us)
        for o in re.findall(r"C-\d+", f[2]):
            if o not in POR_COD:
                dif.append(f"{us}: «otros changes» nombra {o}, que no existe")
            else:
                implementa[o].add(us)
    for us in mapeo:
        if us not in sec:
            dif.append(f"{us}: está en el mapeo pero no es una historia de la v1 de 06")
    for e in ENTRADAS:
        if set(e.historias) != implementa.get(e.cod, set()):
            dif.append(
                f"{e.cod}: el Objetivo cita {sorted(e.historias)} y el mapeo le asigna {sorted(implementa.get(e.cod, set()))}"
            )
    citadas = set(re.findall(r"US-\d{3}", CH))
    for us in sorted(citadas - set(sec)):
        dif.append(f"{us}: citada en este archivo, no existe en 06")
    return f"{len(sec)} historias de 06; {len(citadas & set(sec))} citadas", dif


def fila_3a():
    citadas = set(re.findall(NO_PRECEDIDO + r"(RN-[A-Z]{2}-\d{2}[a-z]?)", CH))
    definidas = set(re.findall(r"^- \*\*(RN-[A-Z]{2}-\d{2}[a-z]?)\*\*", KB["05"], re.M))
    dif = [f"{r}: citada, no definida en 05" for r in sorted(citadas - definidas)]
    return f"{len(citadas)} reglas distintas (05 define {len(definidas)})", dif


def fila_3b():
    citadas = set(re.findall(NO_PRECEDIDO + r"(DD-\d{2})\b", CH))
    definidas = set(re.findall(r"^### (DD-\d{2}) ", KB["09"], re.M))
    dif = [f"{d}: citada, no existe en 09" for d in sorted(citadas - definidas)]
    return f"{len(citadas)} decisiones distintas (09 define {len(definidas)})", dif


def escenarios_de_06():
    tabla = dividir_tabla(KB["06"], "**Escenarios con ID estable**")
    return {f[0] for f in tabla if f and re.fullmatch(r"E\d+", f[0])}


def fila_3c():
    citados = set(re.findall(NO_PRECEDIDO + r"(?<!\.)(E\d{1,2})\b(?!\.)", CH))
    definidos = escenarios_de_06()
    dif = [f"{e}: citado, no existe en la tabla de US-010" for e in sorted(citados - definidos, key=lambda x: int(x[1:]))]
    return f"{len(citados)} escenarios distintos (06 define {len(definidos)})", dif


def rutas_kb():
    """(todas, v1, fase2) de 02 y 03."""
    todas, fase2, v1 = set(), set(), set()
    for k in ("02", "03"):
        for ruta, resto in rutas_de(KB[k]):
            todas.add(ruta)
            (fase2 if "Fase 2" in resto else v1).add(ruta)
    fase2 -= v1
    return todas, v1, fase2


def rutas_citadas():
    return {r for r, _ in rutas_de(CH)}


def fila_4():
    todas, v1, fase2 = rutas_kb()
    cit = rutas_citadas()
    dif = [f"{r}: citada, no figura en 02 ni 03" for r in sorted(cit - todas)]
    return f"{len(cit)} rutas citadas (02 y 03 listan {len(todas)}, {len(fase2)} de ellas de Fase 2)", dif


def nombres_de_entidades():
    """[(nombres, historias que nombra «Change que la crea»)] por encabezado de 04."""
    t = KB["04"]
    ini = t.find("## Entidades")
    fin = t.find("## Subconjunto del primer change")
    cuerpo = t[ini:fin]
    res = []
    for p in re.split(r"^(?=### )", cuerpo, flags=re.M):
        m = re.match(r"### (.*)", p)
        if not m:
            continue
        cab = re.split(r" \(| — ", m.group(1))[0].strip()
        nombres = [n.strip() for n in re.split(r" y | e ", cab)]
        mc = re.search(r"\*\*Change que (?:la|los) crea[n]?:\*\*\s*(.*)", p)
        hist = []
        if mc:
            frase = mc.group(1)
            if frase.lower().startswith("primer change"):
                hist = ["US-010"]
            else:
                mu = re.search(r"US-(\d{3})(?: a US-(\d{3}))?", frase)
                if mu:
                    a, b = int(mu.group(1)), int(mu.group(2) or mu.group(1))
                    hist = [f"US-{x:03d}" for x in range(a, b + 1)]
        res.append((nombres, hist, m.group(1)))
    return res


def fila_5():
    dif = []
    filas = dividir_tabla(CH, "### Tablas del modelo")
    crea = {}
    for f in filas:
        mt = re.fullmatch(r"`(\w+)`", f[0]) if f else None
        if mt:
            if mt.group(1) in crea:
                dif.append(f"{mt.group(1)}: aparece más de una vez en «Tablas del modelo»")
            mc = re.findall(r"C-\d+", f[1])
            crea[mt.group(1)] = mc[0] if len(mc) == 1 else None
    implementa = defaultdict(set)
    for us, filas_m in mapeo_historias().items():
        f = filas_m[0]
        for c in re.findall(r"C-\d+", f[1] + " " + f[2]):
            implementa[c].add(us)
    todas = set()
    for nombres, hist, cab in nombres_de_entidades():
        if not hist:
            dif.append(f"04 §{cab}: no se pudo leer la historia de «Change que la crea»")
        for n in nombres:
            todas.add(n)
            c = crea.get(n)
            if n not in crea:
                dif.append(f"{n}: no tiene fila en «Tablas del modelo → change que las crea»")
            elif c not in POR_COD:
                dif.append(f"{n}: el change que la crea ({c}) no existe")
            else:
                if not (set(hist) & implementa[c]):
                    dif.append(f"{n}: 04 nombra {hist} y {c} implementa {sorted(implementa[c])}")
                if f"`{n}`" not in POR_COD[c].texto:
                    dif.append(f"{n}: la entrada {c} no nombra la tabla")
    for n in sorted(set(crea) - todas):
        dif.append(f"{n}: está en «Tablas del modelo» y no es una entidad de 04")
    return f"{len(todas)} tablas", dif


CITA_CA = re.compile(r"CA-(\d+)([a-z]?)(?: a CA-(\d+))?")


def citas_ca(lineas):
    """[(historia o None, 'CA-n[x]', línea)]; «CA-7 a CA-10» cita todos los del medio."""
    res = []
    for ln in lineas:
        for m in CITA_CA.finditer(ln):
            previas = re.findall(r"US-\d{3}", ln[:m.start()])
            hist = previas[-1] if previas else None
            res.append((hist, f"CA-{m.group(1)}{m.group(2)}", ln))
            if m.group(3):
                for n in range(int(m.group(1)) + 1, int(m.group(3)) + 1):
                    res.append((hist, f"CA-{n}", ln))
    return res


def base(ca):
    """CA-2b se agrupa con CA-2 al contar pares (la letra es una variante del mismo criterio)."""
    return re.match(r"CA-\d+", ca).group(0)


def criterios_de_06():
    crit = set()
    for us, txt in secciones_us(KB["06"]).items():
        for m in re.finditer(r"^- \[[ xX]\] CA-(\d+[a-z]?)\b", txt, re.M):
            crit.add((us, "CA-" + m.group(1)))
    return crit


def fila_6():
    dif = []
    kb = criterios_de_06()
    citas = citas_ca(CH.split("\n"))
    pares = set()
    for us, ca, ln in citas:
        if us is None:
            dif.append(f"{ca} sin historia en su línea: {ln.strip()[:90]}")
        elif (us, ca) not in kb:
            dif.append(f"{us} {ca}: citado, no existe en 06")
        else:
            pares.add((us, base(ca)))
    esc = citas_ca([ln for ln in CH.split("\n") if ln.startswith("- **Escenarios mínimos**")])
    esc_pares = {(u, base(c)) for u, c, _ in esc}
    detalle = f"solo «Escenarios mínimos»: {len(esc)} citas, {len(esc_pares)} pares"
    return (
        f"{len(pares)} criterios distintos (pares historia y CA), en {len(citas)} citas de todo el índice "
        f"(incluye «Leer antes» y el mapeo)",
        dif,
        detalle,
    )


def registro_decisiones():
    ids = set()
    activo = False
    for ln in KB["10"].split("\n"):
        if ln.startswith("## "):
            activo = False
        if ln.startswith("### Decisiones del autor"):
            activo = True
            continue
        if activo and ln.startswith("|"):
            celdas = ln.split("|")
            if len(celdas) > 1:
                ids |= {f"D{n}" for n in re.findall(NO_PRECEDIDO + r"D(\d+)\b", celdas[1])}
    return ids


def fila_7():
    d_cit = set("D" + n for n in re.findall(NO_PRECEDIDO + r"D(\d{1,3})\b", CH))
    su_cit = set(re.findall(NO_PRECEDIDO + r"(SU-\d{2})\b", CH))
    p_cit = set(re.findall(NO_PRECEDIDO + r"(P-\d{2})\b", CH))
    d_reg = registro_decisiones()
    su_def = set(re.findall(r"^### (SU-\d{2}) ", KB["09"], re.M))
    p_def = set(re.findall(r"^\| (P-\d{2}) \|", KB["10"], re.M))
    dif = [f"{d}: citada, no figura en el registro de 10" for d in sorted(d_cit - d_reg, key=lambda x: int(x[1:]))]
    dif += [f"{s}: citada, no existe en 09" for s in sorted(su_cit - su_def)]
    dif += [f"{p}: citada, no existe en 10" for p in sorted(p_cit - p_def)]
    return f"{len(d_cit)} D, {len(su_cit)} SU y {len(p_cit)} P", dif


def fila_8():
    _, v1, _ = rutas_kb()
    cit = rutas_citadas()
    dif = [f"{r}: está en 02 o 03 y ninguna entrada la cita" for r in sorted(v1 - cit)]
    return f"{len(v1)} rutas de la v1", dif


def referencias_leer_antes(e):
    """[(tipo, valor, archivo_kb)] de las líneas de «Leer antes» de una entrada."""
    refs = []
    for ln in e.leer:
        segs = list(re.finditer(r"`knowledge-base/([A-Za-z0-9_.]+\.md)`", ln))
        for k, m in enumerate(segs):
            texto = ln[m.end():segs[k + 1].start() if k + 1 < len(segs) else len(ln)]
            archivo = m.group(1)
            refs.append(("archivo", archivo, archivo))
            for q in re.findall(r"filas?\s+«([^»]*)»", texto):
                refs.append(("fila", q, archivo))
            sin_fila = re.sub(r"filas?\s+«[^»]*»", " ", texto)
            for q in re.findall(r"«([^»]*)»", sin_fila):
                refs.append(("seccion", q, archivo))
            libre = re.sub(r"«[^»]*»", " ", texto)
            for g in re.findall(r"filas?\s+([A-ZÁÉÍÓÚ][\wáéíóúñ]*(?:\s+y\s+[A-ZÁÉÍÓÚ][\wáéíóúñ]*)*)", libre):
                for nombre in re.split(r"\s+y\s+", g):
                    refs.append(("fila", nombre, archivo))
            for v in re.findall(r"§(US-\d{3})", libre):
                refs.append(("id", v, archivo))
            for v in re.findall(r"§([A-Za-zÁÉÍÓÚáéíóúñ][\wÁÉÍÓÚáéíóúñ]*)(?![\w-])", libre):
                refs.append(("encabezado", v, archivo))
            for v in re.findall(r"Flujo (\d+)", libre):
                refs.append(("flujo", v, archivo))
            ids = []
            ids += re.findall(NO_PRECEDIDO + r"(RN-[A-Z]{2}-\d{2}[a-z]?)", libre)
            ids += re.findall(NO_PRECEDIDO + r"(DD-\d{2}|SU-\d{2})\b", libre)
            ids += ["D" + n for n in re.findall(NO_PRECEDIDO + r"D(\d{1,3})\b", libre)]
            ids += re.findall(NO_PRECEDIDO + r"(E\d{1,2})\b(?!\.)", libre)
            ids += [u for u in re.findall(NO_PRECEDIDO + r"(US-\d{3})", libre)
                    if ("§" + u) not in libre]
            for v in ids:
                refs.append(("id", v, archivo))
    return refs


def fila_9():
    dif = []
    n = 0
    existentes = {p.name for p in (RAIZ / "knowledge-base").glob("*.md")}
    for e in ENTRADAS:
        for tipo, valor, archivo in referencias_leer_antes(e):
            n += 1
            if archivo not in existentes:
                if tipo == "archivo":
                    dif.append(f"{e.cod}: el archivo {archivo} no existe")
                continue
            texto = TEXTOS[NOMBRES_KB[archivo]]
            if tipo == "archivo":
                continue
            if tipo == "id":
                patron = NO_PRECEDIDO + re.escape(valor) + r"(?![A-Za-z0-9])"
                ok = re.search(patron, texto) is not None
            elif tipo == "seccion":
                ok = norm(valor) in norm(texto)
            elif tipo == "encabezado":
                ok = any(
                    re.search(r"(?<![\wÁÉÍÓÚáéíóúñ])" + re.escape(valor) + r"(?![\wÁÉÍÓÚáéíóúñ])", h)
                    for h in re.findall(r"^#+ (.*)$", texto, re.M)
                )
            elif tipo == "flujo":
                ok = re.search(rf"^#+ Flujo {valor}\b", texto, re.M) is not None
            elif tipo == "fila":
                ok = any(
                    norm(valor) in norm(ln.split("|")[1])
                    for ln in texto.split("\n")
                    if ln.startswith("|") and len(ln.split("|")) > 2
                )
            else:
                ok = False
            if not ok:
                dif.append(f"{e.cod}: {tipo} «{valor}» no aparece en {archivo}")
    return f"{n} referencias", dif


def arbol():
    ini = CH.find("## Árbol de dependencias")
    bloque = re.search(r"```\n(.*?)\n```", CH[ini:], re.S).group(1).split("\n")
    nodos = {}
    orden_bloque = None
    pila = []
    repetidos = []
    for ln in bloque:
        mb = re.match(r"BLOQUE (\d+) \(orden (\d+)\)", ln)
        if mb:
            orden_bloque = int(mb.group(2))
            pila = []
            continue
        m = re.match(r"^([ │├└─]*)(C-\d+) ([a-z0-9-]+)\s*(?:\(([^)]*)\))?", ln)
        if not m:
            continue
        sangria = len(m.group(1))
        while pila and pila[-1][1] >= sangria:
            pila.pop()
        padre = pila[-1][0] if pila else None
        deps = set(re.findall(r"C-\d+", m.group(4) or ""))
        if padre:
            deps.add(padre)
        if m.group(2) in nodos:
            repetidos.append(m.group(2))
        nodos[m.group(2)] = (m.group(3), orden_bloque, deps)
        pila.append((m.group(2), sangria))
    return nodos, repetidos


def fila_10():
    dif = []
    nodos, repetidos = arbol()
    for c in repetidos:
        dif.append(f"árbol: {c} aparece más de una vez")
    for e in ENTRADAS:
        if e.cod not in nodos:
            dif.append(f"árbol: falta {e.cod}")
            continue
        nombre, bloque, deps = nodos[e.cod]
        if nombre != e.nombre:
            dif.append(f"{e.cod}: nombre del árbol {nombre!r} y de la entrada {e.nombre!r}")
        if bloque != e.orden:
            dif.append(f"{e.cod}: bloque {bloque} en el árbol y Orden {e.orden} en la entrada")
        if deps != set(e.deps):
            dif.append(f"{e.cod}: dependencias del árbol {sorted(deps)} y de la entrada {sorted(e.deps)}")
    for c in sorted(set(nodos) - set(POR_COD)):
        dif.append(f"árbol: {c} no es una entrada")
    ini = CH.find("### Paralelismo por fase")
    puertas = re.search(r"```\n(.*?)\n```", CH[ini:], re.S).group(1)
    for e in ENTRADAS:
        if not re.search(re.escape(e.cod) + r"(?!\d)", puertas):
            dif.append(f"puertas: no nombran {e.cod}")
    # donde la puerta escribe el nombre junto al código («C-06 sesion-con-jwt») debe ser el de la entrada
    for c, n in re.findall(r"(C-\d+) ([a-z0-9]+(?:-[a-z0-9]+)+)", puertas):
        if c in POR_COD and n != POR_COD[c].nombre:
            dif.append(f"puertas: {c} aparece como {n!r} y la entrada dice {POR_COD[c].nombre!r}")
    for c in sorted(set(re.findall(r"C-\d+", puertas)) - set(POR_COD)):
        dif.append(f"puertas: {c} no es una entrada")
    return f"{len(nodos)} nodos", dif


def fila_11():
    dif = []
    ini = CH.find("### Camino crítico")
    sec = CH[ini:]
    cabecera = re.match(r"### Camino crítico \((\d+) changes", sec)
    codigo = re.search(r"```\n(.*?)\n```", sec, re.S).group(1)
    camino = re.findall(r"C-\d+", codigo)
    if cabecera and int(cabecera.group(1)) != len(camino):
        dif.append(f"el título dice {cabecera.group(1)} changes y la cadena tiene {len(camino)}")
    for c in camino:
        if c not in POR_COD:
            dif.append(f"{c}: no existe")
            return f"{len(camino)} changes", dif
    if POR_COD[camino[0]].deps:
        dif.append(f"{camino[0]} abre la cadena y tiene dependencias")
    for a, b in zip(camino, camino[1:]):
        if a not in POR_COD[b].deps:
            dif.append(f"{b} no depende directamente de {a}")
    tope = max(e.orden for e in ENTRADAS)
    mvp = [e for e in ENTRADAS if e.orden < tope]
    mejor = {}

    def largo(c):
        if c not in mejor:
            mejor[c] = 1 + max([largo(d) for d in POR_COD[c].deps if d in POR_COD] or [0])
        return mejor[c]

    maximo = max(largo(e.cod) for e in mvp)
    if len(camino) != maximo:
        dif.append(f"la cadena tiene {len(camino)} changes y la más larga hasta un change del MVP tiene {maximo}")
    if POR_COD[camino[-1]].orden >= tope:
        dif.append(f"{camino[-1]} no es un change del MVP")
    return f"{len(camino)} changes", dif


EMOJI = re.compile("[\U0001F000-\U0001FAFF⌀-⏿☀-➿⬀-⯿️‍]")


def contar_escenarios(linea):
    """Cuenta los escenarios de la línea «Escenarios mínimos» (ver docstring)."""
    # la primera oración termina en el primer «. » fuera de paréntesis
    prof, corte = 0, len(linea)
    for i, ch in enumerate(linea):
        if ch == "(":
            prof += 1
        elif ch == ")":
            prof -= 1
        elif ch == "." and prof == 0 and linea[i + 1:i + 2] in ("", " "):
            corte = i
            break
    prof, items, actual = 0, [], ""
    for ch in linea[:corte]:
        if ch == "(":
            prof += 1
        elif ch == ")":
            prof -= 1
        if prof == 0 and ch in ";,":
            items.append(actual)
            actual = ""
        else:
            actual += ch
    items.append(actual)
    return len([i for i in items if i.strip()])


def fila_12():
    dif = []
    codigos = [e.num for e in ENTRADAS]
    if codigos != list(range(1, len(codigos) + 1)):
        dif.append(f"los códigos no son consecutivos desde C-01: {codigos}")
    vistos = {}
    for e in ENTRADAS:
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", e.nombre):
            dif.append(f"{e.cod}: nombre no kebab-case: {e.nombre!r}")
        if e.nombre in vistos:
            dif.append(f"{e.cod}: nombre repetido con {vistos[e.nombre]}")
        vistos[e.nombre] = e.cod
        if len(e.lineas) > 12:
            dif.append(f"{e.cod}: {len(e.lineas)} líneas (máximo 12)")
        if e.escenarios is None:
            dif.append(f"{e.cod}: sin «Escenarios mínimos»")
        else:
            n = contar_escenarios(e.escenarios)
            lo, hi = (8, 8) if e.cod == "C-01" else (3, 6)
            if not lo <= n <= hi:
                dif.append(f"{e.cod}: {n} escenarios (debe haber {lo} a {hi})" if lo != hi else f"{e.cod}: {n} escenarios (C-01 lleva 8)")
        if not 3 <= len(e.leer) <= 4:
            dif.append(f"{e.cod}: {len(e.leer)} líneas de «Leer antes» (debe haber 3 o 4)")
        if EMOJI.search(e.texto):
            dif.append(f"{e.cod}: tiene un emoji")
    return f"{len(ENTRADAS)} entradas", dif


FILAS = [
    ("1", "Dependencias", fila_1),
    ("2", "Historias", fila_2),
    ("3a", "Reglas", fila_3a),
    ("3b", "Decisiones", fila_3b),
    ("3c", "Escenarios", fila_3c),
    ("4", "Rutas", fila_4),
    ("5", "Tablas", fila_5),
    ("6", "Criterios CA-n", fila_6),
    ("7", "D, SU y P", fila_7),
    ("8", "Rutas sin change", fila_8),
    ("9", "Referencias de «Leer antes»", fila_9),
    ("10", "Árbol y puertas", fila_10),
    ("11", "Camino crítico", fila_11),
    ("12", "Formato", fila_12),
]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(f"Verificación cruzada de {RAIZ / 'CHANGES.md'}")
    total = 0
    for num, titulo, f in FILAS:
        r = f()
        elementos, dif = r[0], r[1]
        total += len(dif)
        print(f"\nFila {num} - {titulo}")
        print(f"  Revisados: {elementos}")
        if len(r) > 2:
            print(f"  Informativo: {r[2]}")
        if dif:
            print(f"  {len(dif)} diferencias:")
            for d in dif:
                print(f"    - {d}")
        else:
            print("  sin diferencias")
    print(f"\nTotal: {total} diferencias" if total else "\nTotal: sin diferencias")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
