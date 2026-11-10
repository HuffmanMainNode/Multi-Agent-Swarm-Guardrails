# Computing and Protocol Glossary for First-Time Readers

Plain-language explanations are starting points, not replacements for normative definitions.

| Term | Plain-language explanation |
|---|---|
| Algorithm | A repeatable method for solving a problem |
| API | A defined way for one program to ask another program for something |
| Application / app | Software designed to perform tasks |
| Authentication | Checking who or what is making a request |
| Authorization | Deciding whether that requester may perform an action |
| Binary | Data represented using bits, commonly 0 and 1 |
| Bug | A defect that makes software behave incorrectly |
| Build | The process of preparing source code into something runnable or distributable |
| Byte | A group of eight bits |
| Capability | A specific authority or ability granted to a system |
| CLI | Command-line interface; a text-based way to use a program |
| Code | Instructions written in a language a computer tool can process |
| Compiler | A tool that translates source code into another form, often machine code |
| Computer language | A broad phrase that can mean programming, markup, query, or machine languages; these are not interchangeable |
| Conformance | Meeting a defined specification, demonstrated by specified checks |
| Cryptography | Mathematical techniques used for things such as encryption, signatures, and integrity checks |
| Data format | Agreed structure for representing information |
| Debug | Find and understand the cause of a defect |
| Dependency | Software or a component another program relies on |
| Encoding | A defined way to represent information as bytes or text |
| Encryption | Transforming information so it cannot be read without the appropriate key |
| Evidence | Information that supports or challenges a claim |
| Fuzzing | Testing software with many generated or mutated inputs to discover unexpected behavior |
| Git | A tool for tracking file changes and collaboration |
| Human language | Languages people use to communicate, such as English, Arabic, Spanish, or Swahili |
| Interoperability | Different systems being able to work together according to shared rules |
| JSON | A common text format for structured data |
| Library / package | Reusable software that other programs can include |
| Machine language | Instructions represented in a form a processor can execute |
| Model | A trained computational system that produces outputs from inputs |
| Open source | Software whose source is made available under a license that grants defined rights |
| Parser | Software that reads input and checks or interprets its structure |
| Permission | An allowed action under a defined authority or policy |
| Protocol | Shared rules for exchanging messages or coordinating behavior |
| Pull request | A proposal to review and merge changes into a project |
| Repository | A project and its files, history, and collaboration records |
| Runtime | The software environment in which a program executes |
| Schema | Rules describing the expected structure and constraints of data |
| Source code | Human-readable instructions used to build or run software |
| Terminal | A text interface for entering commands |
| Test vector | A known input and expected result used to check implementations |
| Tokenizer | A component that splits text into tokens for a language model |
| Translation | Expressing meaning in another human language; exact one-to-one word replacement is not guaranteed |
| Version control | Recording changes so they can be compared, reviewed, and sometimes restored |

## Important distinction: request, authentication, authorization, execution

These are separate concepts:

1. A **request** says what someone wants.
2. **Authentication** checks the identity or credential presented.
3. **Authorization** decides whether the request is permitted.
4. **Execution** performs the operation.
5. **Evidence** records information about what happened.

A request is not permission. A model response is not authentication. A policy decision alone does not prove that every execution path was controlled.
