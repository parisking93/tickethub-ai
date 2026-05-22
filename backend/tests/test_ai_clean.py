"""Test della pulizia dell'output AI (rimozione reasoning/canali)."""

from app.integrations.ai.base import clean_ai_output


def test_harmony_keeps_only_final():
    raw = (
        "<|channel|>analysis<|message|>Sto ragionando…<|end|>"
        "<|channel|>final<|message|>Buongiorno, ecco la risposta.<|return|>"
    )
    assert clean_ai_output(raw) == "Buongiorno, ecco la risposta."


def test_think_block_removed():
    raw = "<think>ragionamento interno</think>Ciao, come stai?"
    assert clean_ai_output(raw) == "Ciao, come stai?"


def test_plain_text_unchanged():
    assert clean_ai_output("Testo pulito.") == "Testo pulito."


def test_code_blocks_preserved():
    raw = "<think>penso</think>### FILE: a.py\n```\nprint('x')\n```"
    out = clean_ai_output(raw)
    assert "### FILE: a.py" in out
    assert "print('x')" in out
