# GitHub Field Guide: From First Profile to Healthy Open-Source Contributor

This guide teaches practical participation on GitHub for first-time users, experienced developers, maintainers, and people working with AI assistants.

GitHub's interface changes over time. The concepts and safety practices here are durable guidance; consult GitHub's current documentation when a button, permission, or policy differs.

## 1. Start with your purpose

Before creating accounts, repositories, forks, or badges, ask:
- What do I want to learn, build, document, or contribute?
- Is this personal work, a community project, school work, or company work?
- Should it be public, private, or shared with a limited group?
- Does it contain secrets, personal data, employer material, or other people's work?
- Who could maintain it if I become unavailable?

Use a profile and repository to make work understandable, not to manufacture activity.

## 2. Build a profile that feels like you

Your GitHub profile is a landing page. It can show your interests, projects, working style, community values, and current focus. It does not need to look like anyone else's.

### Profile README

GitHub supports a special profile repository: create a public repository whose name exactly matches your GitHub username. Its README can appear on your profile when it meets GitHub's profile README requirements.

A useful profile README answers:
1. Who are you, in the terms you choose to share?
2. What are you building or learning?
3. What kinds of collaboration interest you?
4. Which projects should visitors look at first?
5. How can people contact or contribute, if you want contact?

A profile can be playful, calm, technical, artistic, community-focused, or a mixture. A consistent visual theme can make it memorable, but readability, accessibility, and honest project descriptions matter more than decoration.

Keep private details private. Do not publish personal addresses, private email addresses, phone numbers, credentials, access tokens, private schedules, or details that could put anyone at risk. Review every external badge, image, visitor counter, and embedded widget: third-party images can reveal visitor information to their host.

See the [profile README template](../templates/profile/README.md).

## 3. Create a repository with a plan

A repository is a project home with files, history, and collaboration tools. Before creating one:
- Choose a clear, searchable name.
- Write one sentence explaining the problem it addresses.
- Decide the license before accepting outside contributions.
- Choose public or private deliberately. Public repositories are visible to the world.
- Add a README explaining purpose, status, setup, use, contribution, and limitations.
- Add a suitable ignore file for languages and tools.
- Keep secrets and generated build output out of version control.
- Add a security reporting route appropriate to the project's risk.
- Start with a small, coherent structure. Do not create folders merely to make a project look large.

See the [repository README template](../templates/repository/README.md).

### Suggested small project structure

~~~text
project-name/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── .gitignore
├── docs/
├── examples/
├── src/
└── tests/
~~~

This is a starting point, not a mandatory layout. Follow the conventions of the language and ecosystem.

## 4. Understand README files

A README is the front door, not a marketing fog machine. A first-time visitor should answer:
- What is this?
- Who is it for?
- What is its current status?
- What can I actually do with it today?
- How do I install or inspect it?
- How do I test it?
- What does it not do?
- How can I contribute?
- What license applies?

Prefer tested commands, short examples, clear headings, and links to deeper documentation. Label prototypes, mockups, planned features, and untested claims. Never present a roadmap item as implemented.

## 5. Forks, clones, and upstream projects

A fork is a GitHub-hosted copy associated with its upstream repository. A clone is a local copy on your computer. They solve different problems.

### When to fork

Fork when you intend to propose changes to a project you do not control, experiment in an isolated copy, maintain a legitimate derivative, or learn a project's workflow through a bounded exercise.

Do not fork repositories merely to inflate counts, collect trophies, or create abandoned copies. A fork is not a bookmark. Use a watch, star, saved list, or local notes when your goal is simply to follow a project.

### A healthy contribution flow

1. Read the upstream README, license, contribution guide, and security policy.
2. Check whether contributions are welcome and whether an issue already covers the work.
3. Fork the upstream repository when a fork is appropriate.
4. Clone your fork to your computer.
5. Add the original repository as the upstream remote.
6. Create a focused branch for one change.
7. Make the smallest useful change and add tests where appropriate.
8. Fetch and integrate upstream changes before your branch becomes stale.
9. Run documented checks and inspect the final diff.
10. Open a pull request against the correct upstream branch. Explain the problem, solution, tests, and limitations.
11. Keep the fork only if it has an ongoing purpose. Before deleting it, confirm no work or references depend on it.

Example commands (replace placeholders with real URLs):

~~~bash
git clone https://github.com/YOUR-USERNAME/PROJECT.git
cd PROJECT
git remote add upstream https://github.com/ORIGINAL-OWNER/PROJECT.git
git remote -v
git switch -c fix/clear-description
git fetch upstream
git diff
~~~

The exact synchronization command depends on branch policy and local changes. Do not blindly reset or force-push: those operations can discard work. Learn what a command does before running it.

### Fork hygiene

- Prefer one fork per upstream project, not repeated forks for each experiment.
- Use branches inside your fork for separate contributions.
- Keep the fork's purpose and relationship to upstream clear.
- Synchronize deliberately; do not overwrite local work.
- Do not publish secrets, private issues, or private upstream material.
- Respect licenses and attribution requirements.
- Do not submit duplicate low-effort pull requests to gain activity.
- If maintaining a derivative, document what differs and how you track upstream.

## 6. GitHub achievements and profile trophies

GitHub may display achievements or badges for certain activities. Availability, eligibility, and names can change. They are platform decorations, not certifications, professional qualifications, security evidence, or a measure of someone's value.

Healthy approach: learn useful workflows, make meaningful contributions, keep work reviewable, and let achievements happen as a by-product.

Unhealthy approach: spam issues, pull requests, comments, commits, forks, or stars; split trivial changes solely to trigger badges; copy work and claim it; pressure people for stars; or treat trophy count as proof of skill.

The project welcomes people who have never earned a badge and people who ignore them entirely.

## 7. Organize repositories and projects

A clean account is easier for humans and AI tools to understand.
- Use descriptive repository names and short descriptions.
- Pin a small number of representative projects rather than every repository.
- Group related work through topics, organizations, or a clear index README where useful.
- Mark archived, experimental, educational, and production-intended projects honestly.
- Keep licenses, ownership, maintainers, and contribution expectations clear.
- Use issues for discrete work, discussions for open-ended conversation, and pull requests for proposed changes.
- Close stale work with a reason rather than silently abandoning it.
- Use milestones and project boards only when they help coordinate real work.
- Review dependencies and automated workflows; remove unused or untrusted automation.
- Maintain backups for important work. Git hosting is not your only backup.

Avoid creating a new repository for every small note. A coherent folder, issue, or document may be better.

## 8. Directing an AI assistant to help with GitHub

AI can explain unfamiliar terms, draft documentation, inspect code, propose tests, and help navigate Git. It can also hallucinate repository facts, recommend destructive commands, introduce insecure dependencies, or claim work was tested when it was not.

Use the [AI project brief template](../templates/ai-project-brief.md).

A safe instruction pattern:
- State the repository and exact goal.
- Ask the assistant to inspect before editing.
- Identify files it may and may not change.
- Require a plan before high-impact changes.
- Require tests and actual command output.
- Ask for a final diff and limitations.
- Require explicit approval before publishing, merging, deleting, changing permissions, or running destructive commands.

Never paste credentials, private keys, access tokens, private user data, or confidential source code into an unapproved AI service. Use least-privilege access and review connected-app permissions.

## 9. International collaboration

Open source crosses borders, time zones, languages, and technical cultures.
- Explain acronyms and local assumptions.
- Do not assume everyone uses the same operating system, keyboard, payment system, network, or development environment.
- Be patient with language differences; ask clarifying questions instead of mocking phrasing.
- Preserve a contributor's meaning when editing their words.
- Label machine translations as drafts until a competent human reviews them.
- Record timezone explicitly when scheduling.
- Credit ideas and work accurately.
- Share the problem and reasoning, not only the final code. "This is how we solved it" is valuable knowledge.

## 10. A healthy first contribution

A good first contribution might fix a confusing README sentence, report a broken setup command, add a missing example, improve keyboard navigation, review a translation you know well, reproduce a bug with private information removed, or add a test for documented behavior.

Small, truthful, reviewable work is more valuable than impressive-looking activity.

## 11. Check before publishing

- [ ] I understand whether this repository is public or private.
- [ ] I have a suitable license or explained why one is not yet chosen.
- [ ] No secrets, credentials, or private data are included.
- [ ] The README describes the actual current state.
- [ ] Commands and examples have been tested or clearly labeled untested.
- [ ] I checked licenses and attribution for reused material.
- [ ] I know who can review and maintain the project.
- [ ] I inspected the final changes.
- [ ] AI assistance has been reviewed and disclosed where relevant.
- [ ] I am contributing for a useful purpose, not platform noise.
