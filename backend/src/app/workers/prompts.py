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


def _priority_note(review_note: str | None) -> str:
    if not review_note:
        return ""
    return (
        ">>> ISTRUZIONE PRIORITARIA DELL'UTENTE (ha la precedenza su tutto il resto, "
        f"rispettala alla lettera): {review_note}"
    )


def build_email_prompt(ticket: Ticket, conversation: str, attachments_text: str = "") -> str:
    parts = [
        _priority_note(ticket.review_note),
        "Ecco la conversazione email completa (dal più vecchio al più recente):",
        "---",
        conversation or (ticket.description or ticket.title),
        "---",
        "Considera l'INTERO scambio qui sopra per capire il contesto e cosa è già stato detto.",
    ]
    if attachments_text:
        parts.append("\nContenuto degli allegati testuali:")
        parts.append(attachments_text)
    parts.append("Scrivi la bozza di risposta all'ultimo messaggio ricevuto.")
    return "\n".join(p for p in parts if p)


CODEGEN_SYSTEM = (
    "Sei un assistente sviluppatore senior. Applichi modifiche di codice a un repository. "
    "Rispondi SOLO con i file da scrivere, ognuno in questo formato esatto:\n"
    "### FILE: percorso/relativo.ext\n"
    "```\n"
    "<contenuto COMPLETO del file>\n"
    "```\n"
    "Regole tassative:\n"
    "- Per ogni file modificato includi il suo contenuto INTERO, non frammenti.\n"
    "- PRESERVA tutto il codice esistente che non è interessato dalla modifica: "
    "parti dal contenuto attuale del file e applica solo le modifiche necessarie.\n"
    "- Includi solo i file che cambiano. Usa percorsi relativi alla radice del repo.\n"
    "- Nessuna spiegazione fuori dai blocchi."
)


def build_codegen_prompt(ticket: Ticket, file_tree: str, files_content: dict[str, str]) -> str:
    parts = [
        _priority_note(ticket.review_note),
        f"Tipo richiesta: {ticket.type.value}",
        f"Titolo: {ticket.title}",
        "Descrizione:",
        ticket.description or "(nessuna descrizione)",
    ]

    parts.append("\nStruttura del repository (file tracciati):")
    parts.append(file_tree)

    if files_content:
        parts.append("\nContenuto attuale dei file (preservalo dove non va modificato):")
        for path, content in files_content.items():
            parts.append(f"\n### FILE: {path}\n```\n{content}\n```")

    parts.append("\nProduci i file da creare o modificare per soddisfare la richiesta.")
    return "\n".join(p for p in parts if p)


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
