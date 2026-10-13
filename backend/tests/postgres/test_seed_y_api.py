"""Perfil opcional con PostgreSQL: el seed y la API sobre la base migrada (design I12, I13).

Sin mocks: sesiones, aplicación y base reales. El esquema sale de las migraciones (I9).
"""
import pytest
from sqlalchemy.orm import Session

from app.infrastructure.db.modelos import PacienteModelo
from app.infrastructure.db.seed_demo import ajustar_secuencias, cargar_demo_si_falta

pytestmark = pytest.mark.postgres


def test_despues_del_seed_se_puede_crear_un_paciente_sin_id(sesion: Session):
    assert cargar_demo_si_falta(sesion) is True
    ajustar_secuencias(sesion)

    nuevo = PacienteModelo(
        consultorio_id=1, nombre="Diego", apellido="Imaginario", telefono_whatsapp="+5491155550104"
    )
    sesion.add(nuevo)
    sesion.commit()

    # El seed fijó los identificadores 1 a 3: sin ajustar la secuencia el alta chocaría con el 1.
    assert nuevo.id == 4
