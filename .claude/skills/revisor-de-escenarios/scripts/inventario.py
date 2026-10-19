"""Inventario de escenarios de un change OpenSpec de turnos-odontologia.

Uso (desde la raíz del repositorio):
    python .claude/skills/revisor-de-escenarios/scripts/inventario.py <change>

<change> es el nombre kebab-case (busca en openspec/changes/ y en
openspec/changes/archive/) o la ruta a la carpeta del change.

Imprime en Markdown: los criterios de aceptación mínimos que CHANGES.md pide
para el change, cada escenario de las specs con su tipo, sus códigos RN y si
aparece en tasks.md, los códigos RN que no existen en la KB y los CA mínimos
sin escenario. No juzga la calidad: es la base objetiva para la revisión.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path.cwd()
PATRON_RN = re.compile(r"RN-[A-Z]{2}-\d{2}[a-z]?")
PATRON_CA = re.compile(r"(US-\d{3})\s+(CA-\d+)")
PATRON_E = re.compile(r"\bE\d{1,2}\b")
TIPOS = (
    ("error de negocio", "Error de negocio"),
    ("error de formato", "Error de formato"),
    ("error de entrada", "Error de formato"),
    ("error de acceso", "Error de acceso"),
    ("feliz", "Feliz"),
    ("borde", "Borde"),
    ("error", "Error (sin clasificar)"),
)


def ubicar_change(arg: str) -> Path:
    ruta = Path(arg)
    if ruta.is_dir():
        return ruta
    activo = RAIZ / "openspec" / "changes" / arg
    if activo.is_dir():
        return activo
    archivados = sorted((RAIZ / "openspec" / "changes" / "archive").glob(f"*-{arg}"))
    if archivados:
        return archivados[-1]
    sys.exit(f"No encuentro el change «{arg}» en openspec/changes/ ni en el archivo.")


def nombre_del_change(carpeta: Path) -> str:
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", carpeta.name)


def ca_minimos(nombre: str) -> list[str]:
    changes = (RAIZ / "CHANGES.md").read_text(encoding="utf-8")
    bloque = re.search(rf"### \[C-\d+\] `{re.escape(nombre)}`(.*?)(?=\n### |\Z)", changes, re.S)
    if not bloque:
        return []
    linea = re.search(r"\*\*Escenarios mínimos\*\*:\s*(.+)", bloque.group(1))
    if not linea:
        return []
    minimos: list[str] = []
    for us, cas in re.findall(r"(US-\d{3}):\s*([^;]+)", linea.group(1)):
        for ca in re.findall(r"CA-\d+", cas):
            minimos.append(f"{us} {ca}")
    return minimos


def codigos_de_la_kb() -> set[str]:
    texto = (RAIZ / "knowledge-base" / "05_reglas_de_negocio.md").read_text(encoding="utf-8")
    return set(PATRON_RN.findall(texto))


def escenarios(carpeta: Path) -> list[dict[str, object]]:
    encontrados: list[dict[str, object]] = []
    for spec in sorted(carpeta.glob("specs/*/spec.md")):
        lineas = spec.read_text(encoding="utf-8").splitlines()
        for i, linea in enumerate(lineas):
            if not linea.startswith("#### Scenario:"):
                continue
            titulo = linea.removeprefix("#### Scenario:").strip()
            cuerpo: list[str] = []
            for siguiente in lineas[i + 1:]:
                if siguiente.startswith("#"):
                    break
                cuerpo.append(siguiente)
            texto = " ".join(cuerpo)
            tipo = next((t for clave, t in TIPOS if clave in titulo.lower()), "Sin tipo en el título")
            encontrados.append({
                "spec": spec.parent.name,
                "linea": i + 1,
                "titulo": titulo,
                "tipo": tipo,
                "ca": [f"{us} {ca}" for us, ca in PATRON_CA.findall(titulo)],
                "e": PATRON_E.findall(titulo),
                "rn": sorted(set(PATRON_RN.findall(texto + " " + titulo))),
                "given_when_then": all(k in texto for k in ("WHEN", "THEN")),
            })
    return encontrados


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    carpeta = ubicar_change(sys.argv[1])
    nombre = nombre_del_change(carpeta)
    tareas_ruta = carpeta / "tasks.md"
    tareas = tareas_ruta.read_text(encoding="utf-8") if tareas_ruta.exists() else ""
    kb = codigos_de_la_kb()
    lista = escenarios(carpeta)
    minimos = ca_minimos(nombre)

    print(f"# Inventario de `{nombre}`\n")
    print(f"Carpeta: `{carpeta.relative_to(RAIZ) if carpeta.is_relative_to(RAIZ) else carpeta}`")
    print(f"CA mínimos según CHANGES.md: {', '.join(minimos) or '(no se encontraron)'}\n")

    print("| # | Spec:línea | Tipo | CA | RN | WHEN/THEN | CA en tasks.md |")
    print("|---|---|---|---|---|---|---|")
    for n, esc in enumerate(lista, 1):
        cas = esc["ca"] or esc["e"]
        en_tareas = all(c in tareas for c in cas) if cas else False
        print(
            f"| {n} | {esc['spec']}:{esc['linea']} | {esc['tipo']} | {', '.join(cas) or '—'} | "
            f"{', '.join(esc['rn']) or '—'} | {'sí' if esc['given_when_then'] else 'NO'} | "
            f"{'sí' if en_tareas else 'NO'} |"
        )

    conteo: dict[str, int] = {}
    for esc in lista:
        conteo[str(esc["tipo"])] = conteo.get(str(esc["tipo"]), 0) + 1
    print("\n## Resumen")
    print(f"- Escenarios: {len(lista)} · por tipo: " + ", ".join(f"{t} {c}" for t, c in sorted(conteo.items())))
    for tipo in ("Feliz", "Error de negocio", "Borde"):
        if tipo not in conteo:
            print(f"- FALTA al menos un escenario de tipo «{tipo}» (regla de specs de openspec/config.yaml).")
    cubiertos = {ca for esc in lista for ca in esc["ca"]}
    faltantes = [ca for ca in minimos if ca not in cubiertos]
    if faltantes:
        print(f"- CA mínimos sin escenario: {', '.join(faltantes)}")
    inexistentes = sorted({rn for esc in lista for rn in esc["rn"]} - kb)
    if inexistentes:
        print(f"- Códigos RN que no están en knowledge-base/05_reglas_de_negocio.md: {', '.join(inexistentes)}")
    sin_rn = [str(esc["titulo"]) for esc in lista if esc["tipo"] == "Error de negocio" and not esc["rn"]]
    if sin_rn:
        print("- Errores de negocio sin código RN: " + "; ".join(sin_rn))
    if not tareas:
        print("- No hay tasks.md: no se puede cruzar la verificación de los escenarios.")


if __name__ == "__main__":
    main()
