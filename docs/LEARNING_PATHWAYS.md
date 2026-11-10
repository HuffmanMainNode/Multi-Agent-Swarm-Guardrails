# Learning Pathways: From First Click to Independent Contributor

This guide treats learning as a set of paths, not a ladder of human worth. People arrive with different strengths, devices, languages, access needs, and amounts of time. A person may be advanced in one area and a beginner in another.

## The learning loop

Every pathway uses the same loop:

1. **See it:** observe a real example.
2. **Name it:** learn the words needed to describe it.
3. **Try it:** make one small, bounded attempt.
4. **Check it:** compare the result with an expected outcome.
5. **Explain it:** describe what happened in your own words.
6. **Choose:** repeat, go deeper, or explore a different path.

A learner can stop after any step and still have made progress.

## Path 0: I am completely new

**Goal:** Understand what this project is without installing anything.

1. Complete [Start Here](START_HERE.md#your-first-10-minutes).
2. Read the plain-language map of a repository.
3. Open the example request and policy in GitHub.
4. Identify who is asking, what they want, what resource is involved, and what rule applies.
5. Explain why a request is not the same as permission.

**Done means:** You can explain the request/permission distinction. No code required.

## Path 1: I want to understand computers and code

Learn these concepts in order, using any computer you have access to:

1. Files and folders: create, rename, copy, and find a harmless text file.
2. Text versus program: a text file can contain instructions, but not every text file is executable code.
3. Data: structured information such as JSON is text arranged according to rules.
4. Programs: code describes operations a computer can perform.
5. Input and output: a program reads something, performs work, and produces a result.
6. Tests: a test checks a claim about program behavior.
7. Versions: Git records changes so work can be compared and recovered.
8. Networks and protocols: systems exchange messages according to agreed rules.

Do not rush to the terminal. A graphical file browser and a text editor are enough for the first concepts.

## Path 2: First small code change

**Goal:** Make a documentation-only change before changing executable code.

1. Open the repository on GitHub.
2. Read [CONTRIBUTING](../CONTRIBUTING.md).
3. Find a sentence in the documentation that is unclear to you.
4. Use GitHub's edit-in-browser feature to propose a clearer sentence on a new branch.
5. Explain what confused you and why your wording is clearer.
6. Open a pull request and ask for review.

Do not edit security rules, authorization behavior, schemas, or cryptographic code as a first change. Documentation changes still require review, and a reviewer may suggest a different wording.

**Done means:** You have proposed a small change and can explain it. A pull request is a proposal, not proof that the change is correct or merged.

## Path 3: First local test

**Goal:** Run the project's existing checks without changing security behavior.

Prerequisites: Python 3.11 or newer. Use a disposable development environment, not a production machine.

```bash
git clone https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails.git
cd Multi-Agent-Swarm-Guardrails
python -m venv .venv
```

Activate the environment:

- Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

Then:

```bash
python -m pip install -e ".[dev]"
masg verify --root .
python -m unittest discover -s tests -v
```

If a command fails, keep the exact error text (remove usernames, paths, tokens, and other private details) and ask for help. A failed check is information. Do not hide it or claim success.

## Path 4: Contributor and reviewer

**Goal:** Make a change that can be independently evaluated.

- Read the relevant contract, threat model, schema, implementation, and tests.
- State the behavior before changing it.
- Add positive and negative tests.
- Run the relevant test suite.
- Explain compatibility and residual limitations.
- Ask someone else to review security-sensitive changes.

A green test suite is evidence about the tests that ran. It is not proof of total security or production readiness.

## Path 5: Expert and independent implementer

**Goal:** Build an implementation that does not depend on the reference language.

- Start with normative specifications, schemas, and versioned vectors.
- Implement parsing and semantics independently.
- Run the same positive and negative vectors.
- Publish exact versions, test commands, results, and known deviations.
- Add differential tests and fuzzing where appropriate.
- Avoid claiming conformance beyond the tested surface.

Expertise is demonstrated by reproducible work, clear assumptions, careful testing, and honest limits, not by title or confidence.

## Contributions without coding

You can help by:

- Reporting a confusing sentence or unexplained acronym.
- Reviewing whether a beginner can follow a guide without outside knowledge.
- Checking whether a translation sounds natural in your language.
- Recording a screen-reader, keyboard, mobile, or low-bandwidth accessibility issue.
- Asking a question that reveals an assumption the maintainers overlooked.
- Comparing the documentation with what the software actually does.
- Suggesting a real-world example, with private information removed.

A report should say what you tried, what you expected, what happened, and what would have helped. You do not need to diagnose the underlying code.

## Device and access realities

Not everyone has a modern laptop, reliable internet, administrator rights, or a large data plan.

- Prefer reading and small text files before heavyweight tools.
- Keep core examples small and offline-friendly.
- Do not require a paid service or hosted account for core learning.
- Clearly label optional tools and their resource requirements.
- Provide copyable text alternatives to diagrams and screenshots.
- Avoid assuming Windows, macOS, or Linux.
- Treat mobile-only participation as valid, while being honest when a task requires a desktop development environment.

## Learning progress is not a certification

Finishing a path means you completed its learning activities. It does not certify professional competence, security expertise, or implementation conformance. Those require separate evidence and review.
