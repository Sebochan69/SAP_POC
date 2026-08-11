# SARAP mag SAP

SARAP mag SAP is a local, chat-based assistant for SAP time and leave booking.

## Working rules

- Build one small, end-to-end vertical slice at a time.
- OMP owns implementation and tests; Pi owns requirements, coordination, and review.
- Feature 1 is dry-run only. Do not connect to SAP, Edge, or click any real submission control.
- Ollama is the local model runtime. Validate every model response against a strict schema.
- Never guess an ambiguous leave code or duration; ask for clarification.
- Keep logs structured and redact raw user text, HR data, credentials, and tokens by default.
- Every feature must leave one repeatable verification command and update `docs/HANDOFF.md`.
- Use `.agent-context/` for coordination between Pi and OMP; read `task.md` before coding and write findings/results back there.

## Known SAP mappings

- `0200` = sickness
- `0600` = paid leave (including maternal/paternal leave)

These mappings are only the currently confirmed POC mappings. Do not invent additional codes.
