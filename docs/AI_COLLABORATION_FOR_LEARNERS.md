# AI Collaboration Guide for Learners and Contributors

This guide explains how people and AI assistants can work together without turning confidence into false authority.

## AI can be a tutor, pair programmer, reviewer, or translator

State which role you want. For example:

- **Tutor:** explain one idea at a time and check understanding.
- **Guide:** help me navigate files and tools without making changes.
- **Pair programmer:** propose a small patch and explain every changed line.
- **Reviewer:** look for defects, missing tests, unsafe assumptions, and unclear claims.
- **Translator:** draft a translation, preserve message IDs, identify ambiguity, and mark it unreviewed.

An AI role is a requested mode of assistance, not proof that the system is qualified or correct.

## A reusable beginner prompt

> I am new to this task. Please act as a patient technical guide. Start by telling me the goal in plain language. Explain unfamiliar terms before using them. Break the work into small steps and wait for me when a decision is needed. For each command or code change, explain what it does, what it can affect, how to verify it, and how to undo it. Prefer free, offline, open-source tools. Do not claim you ran a test or changed a file unless you actually did. Clearly separate facts, assumptions, suggestions, and unknowns.

## A reusable review prompt

> Review this proposed change as an independent reviewer. Identify the intended behavior, changed files, assumptions, security impact, compatibility impact, missing negative tests, and ways it could fail. Do not assume the author's explanation is correct. Distinguish issues you reproduced from risks you inferred. Give exact evidence and commands. Do not claim production readiness from passing unit tests alone.

## Human control and safe collaboration

- Ask before allowing an AI agent to modify files, publish branches, merge pull requests, install software, or run commands with side effects.
- Review commands before running them, especially commands involving deletion, permissions, networking, credentials, or system configuration.
- Use a disposable workspace for experiments.
- Never provide passwords, API keys, private keys, recovery codes, personal records, or confidential information.
- Keep an untouched copy of important work and know how to revert changes.
- Treat generated code, translations, documentation, and test results as proposals until checked.
- A model saying "verified" is not verification. Look for the actual command, environment, output, and scope.

## Learning without exposing hidden reasoning

Ask an AI for a concise explanation, assumptions, evidence, alternatives, and a checkable summary. Do not require private internal reasoning or treat a generated explanation as a transcript of hidden cognition. Useful collaboration depends on inspectable results, not claims about inaccessible internal thought.

## Translation safety

Machine-generated translations must remain marked as drafts until reviewed under the project's language-pack rules. Never translate stable protocol identifiers, field names, enum values, or cryptographic inputs unless a normative specification explicitly defines that behavior. When meaning is ambiguous, preserve the source text and flag the ambiguity rather than inventing certainty.
