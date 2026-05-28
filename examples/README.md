# Beispiele

Diese Datei [sample-policy.md](./sample-policy.md) ist **fiktiv** und dient
ausschließlich zum lokalen Ausprobieren von `ingest` und `ask`.

```bash
nis2-rag ingest examples/sample-policy.md
nis2-rag ask "Innerhalb welcher Frist müssen Sicherheitsvorfälle gemeldet werden?"
```

## Eigene Quellen ergänzen

Lege weitere `.pdf`, `.md` oder `.txt` Dateien hier ab und indiziere sie:

```bash
nis2-rag ingest pfad/zu/deinem-dokument.pdf
```

Echte NIS2- und KRITIS-Referenztexte (Gesetzestext, BSI-Orientierungshilfen,
DVO 2024/2690) werden bewusst **nicht mitgeliefert** — Quelle und Aktualität
muss der Anwender selbst sicherstellen.
