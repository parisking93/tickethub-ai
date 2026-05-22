"""Prompt per l'AI worker (in italiano)."""

from __future__ import annotations

from app.models.ticket import Ticket

EMAIL_SYSTEM = (
    "Sei un assistente che redige bozze di risposta a email di assistenza, in italiano. "
    "Scrivi in tono professionale e cortese. Rispondi SOLO con il corpo dell'email, "
    "senza oggetto, senza commenti e senza segnaposto tra parentesi."
)

CODE_SYSTEM = (
    "Sei un assistente sviluppatore senior. Analizzi richieste di fix o feature e proponi "
    "un piano di intervento conciso e concreto, in italiano. Rispondi con un elenco puntato "
    "dei passi e dei file probabilmente coinvolti. Non scrivere codice completo."
)


def build_email_prompt(ticket: Ticket) -> str:
    parts = [
        "Ecco l'email ricevuta a cui rispondere:",
        "---",
        ticket.description or ticket.title,
        "---",
    ]
    if ticket.review_note:
        parts.append(
            "L'utente ha chiesto di rivedere la bozza precedente con queste indicazioni: "
            f"{ticket.review_note}"
        )
    parts.append("Scrivi la bozza di risposta.")
    return "\n".join(parts)


CODEGEN_SYSTEM = (
    "Sei un assistente sviluppatore senior. Applichi modifiche di codice a un repository. "
    "Rispondi SOLO con i file da scrivere, ognuno in questo formato esatto:\n"
    "### FILE: percorso/relativo.ext\n"
    "```\n"
    "<contenuto COMPLETO del file>\n"
    "```\n"
    "Includi l'intero contenuto del file (non frammenti). Non aggiungere spiegazioni "
    "fuori dai blocchi. Usa percorsi relativi alla radice del repository."
)


def build_codegen_prompt(ticket: Ticket, file_tree: str) -> str:
    parts = [
        f"Tipo richiesta: {ticket.type.value}",
        f"Titolo: {ticket.title}",
        "Descrizione:",
        ticket.description or "(nessuna descrizione)",
    ]
    if ticket.review_note:
        parts.append(f"Note di revisione dall'utente da tenere in conto: {ticket.review_note}")
    parts.append("\nStruttura attuale del repository (file principali):")
    parts.append(file_tree)
    parts.append("\nProduci i file da creare o modificare per soddisfare la richiesta.")
    return "\n".join(parts)


def build_code_prompt(ticket: Ticket) -> str:
    parts = [
        f"Tipo richiesta: {ticket.type.value}",
        f"Titolo: {ticket.title}",
        "Descrizione:",
        ticket.description or "(nessuna descrizione)",
    ]
    if ticket.review_note:
        parts.append(f"Note di revisione dall'utente: {ticket.review_note}")
    parts.append("Proponi il piano di intervento.")
    return "\n".join(parts)
