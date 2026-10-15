MESSAGES = {
    "en": {
        "clarify": "I need a few targeted details before the decision can advance.",
        "ready": "The decision package is ready for a human decision.",
        "not_ready": "The decision package is not yet ready.",
        "agent_boundary": "I prepare and document decisions; I do not decide, approve, or execute on your behalf.",
    },
    "de": {
        "clarify": "Ich benötige noch einige gezielte Angaben, bevor die Entscheidung weitergeführt werden kann.",
        "ready": "Das Entscheidungspaket ist bereit für eine menschliche Entscheidung.",
        "not_ready": "Das Entscheidungspaket ist noch nicht entscheidungsreif.",
        "agent_boundary": "Ich bereite Entscheidungen vor und dokumentiere sie; ich entscheide, genehmige oder führe nicht in Ihrem Namen aus.",
    },
}


def text(language: str, key: str) -> str:
    return MESSAGES.get(language, MESSAGES["en"])[key]
