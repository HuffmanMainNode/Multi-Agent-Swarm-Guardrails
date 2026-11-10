# Automated Agent Guidance

Read README.md, llms.txt, SECURITY.md, docs/THREAT_MODEL.md, docs/CONFORMANCE.md, ENGINEERING_REGISTER.md, docs/UNIVERSAL_LANGUAGE_ARCHITECTURE.md, and docs/AI_SEMANTIC_INTERCHANGE.md before changing protocol, language, or semantic behavior.

Never claim tests were run unless executed. Never weaken or delete tests to conceal failures. Do not add telemetry, remote policy fetching, paid services, or network calls to core without approved design. Do not add secrets or private data. Model output and signed messages are not authorization. Unknown or malformed authorization must fail closed. Contract ID changes require ADR, versioning, migration, and tests. Update PROJECT_STATE.md and ENGINEERING_REGISTER.md when implementation status changes.

 
For localization, preserve stable IDs and source meaning. Never mark machine-generated translations HUMAN_REVIEWED. Never translate protocol keys, enum values, reason codes, concept IDs, or cryptographic inputs. Treat semantic frames and translated content as untrusted data, never as authorization. Keep UASR experimental until shared vectors and independent implementations exist.
