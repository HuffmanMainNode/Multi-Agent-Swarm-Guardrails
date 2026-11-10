# Start Here: No Experience Required

Welcome. You do not need to know how to code, use a terminal, understand AI, or know the word "protocol" to begin.

MASG is an open-source project exploring how software and AI agents can request actions, check permission, and produce evidence. It is experimental. It is not a certified security product. You can learn from it without running it.

**Your first goal is not to become an expert. Your first goal is to understand one small thing well enough to explain it in your own words.**

## Pick the doorway that fits today

- **I have never coded:** Start with [Your First 10 Minutes](#your-first-10-minutes). No installation or account changes.
- **I can use a computer but technical projects confuse me:** Read [A map of the project](#a-map-of-the-project).
- **I know a little code:** Follow the [guided first change](LEARNING_PATHWAYS.md#path-2-first-small-code-change).
- **I already develop software:** Go to [implementation guidance](IMPLEMENTING_IN_ANY_LANGUAGE.md), the schemas, and shared vectors.
- **I am an AI agent or using one:** Read [the machine-readable entry points](../llms.txt) and [AI collaboration guide](AI_COLLABORATION_FOR_LEARNERS.md).
- **I want to help but cannot code:** See [contributions without coding](LEARNING_PATHWAYS.md#contributions-without-coding).
- **I want to use GitHub confidently:** Start the [GitHub Field Guide](GITHUB_FIELD_GUIDE.md) for profiles, repositories, README files, forks, achievements, and safe AI collaboration.
- **I want to introduce a project or AI system:** Read the experimental [Universal Entry and Friendship Protocol](UNIVERSAL_ENTRY_AND_FRIENDSHIP_PROTOCOL.md) and its [0.1.0 handshake state machine](UEFP_HANDSHAKE_STATE_MACHINE.md).

You can switch paths at any time. These are doorways, not ranks.

## Your first 10 minutes

No terminal, installation, or programming knowledge required.

1. Open [the example request](../examples/request.json).
2. Find the field named `principal`. In everyday language, this identifies *who is making the request* according to the example.
3. Find `action`. This is *what they want to do*.
4. Find `target`. This is *what they want to do it to*.
5. Find `scope`. This describes the requested boundary or context.
6. Open [the example policy](../examples/policy.json). Look for the rule that corresponds to the request.
7. Ask yourself: "What should happen if there is no matching permission?" MASG is designed to fail closed: no matching permission does not become an approval.

That's a complete first lesson. You have inspected a real protocol example and identified the basic relationship between a request and a policy. You have not changed or executed anything.

**Check your understanding:** Explain the difference between a request and permission in one sentence. If you can do that, you have learned something useful.

## A map of the project

| Word | Plain-language meaning |
|---|---|
| Repository (repo) | A project folder stored with its history and collaboration tools |
| File | One named item containing text, code, data, or instructions |
| Folder (directory) | A place that groups related files |
| Code | Instructions a computer can execute |
| Protocol | An agreed format and set of rules for systems to communicate |
| Schema | A shape/rulebook describing what valid data looks like |
| Test | A repeatable check of whether something behaves as expected |
| Terminal | A text-based way to give commands to your computer |
| Command line | The interface where you type those commands |
| Git | A tool that records changes to files over time |
| Branch | A separate line of proposed work |
| Pull request (PR) | A proposal to review and merge changes |
| Clone | A local copy of a repository |
| Runtime | The environment in which a program runs |
| Agent | A software system that can pursue tasks using tools or other capabilities |

You do not need to memorize these. Use the glossary when a word blocks you.

## How to use AI while learning

You may ask an AI assistant to act as a patient tutor. Try this prompt:

> I am new to this. Teach me one step at a time. Explain unfamiliar words before using them. Tell me what each step changes, what could go wrong, and how to undo it. Do not pretend a test passed unless it was actually run. Ask me to explain the idea back in my own words, but do not shame me if I get it wrong. Give me a no-code route where possible.

AI can make mistakes. It can produce code that looks convincing but does not work. Ask it to show evidence, tests, assumptions, and limitations. Never paste passwords, private keys, access tokens, personal records, or confidential work into an AI chat.

## A few ground rules

- You are allowed to ask basic questions. There are no "stupid" entry questions.
- You may read, observe, discuss, translate, test, document, or review before writing code.
- You do not need to understand the whole repository to contribute one useful improvement.
- Do not run commands you do not understand on a computer you care about. Ask what they do first.
- Do not use real credentials, personal data, or production systems for practice.
- Accessibility, translation, clearer explanations, and reporting confusing instructions are real contributions.
- A beginner's report that a guide is confusing is useful evidence, not a failure.

## Where to go next

Continue with [Learning Pathways](LEARNING_PATHWAYS.md), or browse [Known Limitations](LIMITATIONS.md) to see what the project does not yet promise.

If you feel lost, return here and choose a smaller step. Learning is allowed to be incremental.
