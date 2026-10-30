"""Bajas y reclamaciones en español y valenciano (fork de El Faro).

La detección fija de bajas tiene que funcionar sin el modelo: una baja que
solo reconoce el clasificador puede perderse, y eso no se negocia.
"""
import pytest

from harvey.agents.handler import ESCALATION_PATTERNS, _flat, _opt_out_reason
from harvey.config import ComplianceConfig


@pytest.mark.parametrize("reply", [
    "Baja",
    "baja.",
    "No, gracias.",
    "Por favor, dadme de baja de vuestra lista",
    "No me escribáis más",
    "Borrad mis datos, gracias",
    "Doneu-me de baixa",
])
def test_a_spanish_opt_out_is_honoured_without_the_model(reply):
    assert _opt_out_reason(reply, reply) is not None


@pytest.mark.parametrize("reply", [
    # «baja» dentro de otra palabra no es una baja.
    "Mi hija trabaja aquí, ¿de qué va?",
    "Hola, ¿cuánto cuesta un vídeo?",
    "La temporada baja empieza en noviembre, escríbeme entonces",
])
def test_an_ordinary_spanish_reply_is_not_an_opt_out(reply):
    assert _opt_out_reason(reply, reply) is None


@pytest.mark.parametrize("reply", [
    "Esto lo voy a denunciar a la AEPD",
    "Se lo paso a mi abogado",
    "Esto es spam",
])
def test_a_spanish_complaint_goes_to_a_human(reply):
    assert any(p in _flat(reply) for p in ESCALATION_PATTERNS)


def test_a_spanish_opt_out_line_is_accepted():
    line = "Si no quieres que te escriba más, responde «baja» y no volverás a saber de mí."
    assert ComplianceConfig(opt_out_line=line).opt_out_line == line


def test_a_spanish_line_that_asks_for_nothing_is_still_refused():
    with pytest.raises(ValueError):
        ComplianceConfig(opt_out_line="Si no te interesa, dímelo.")
