# MASG Protocol v1.0.0 Test Vectors

Portable policy and authorization-decision fixtures. Every implementation should consume these unchanged. A vector pass covers only the stated semantic case, not deployment security.

Files: `decision-vectors.json`.


## Shared raw-parser negative fixtures

`parser-negative-vectors.json` contains malformed raw-document cases shared unchanged across Python, Go, Rust, and JavaScript. Raw documents are encoded as lowercase hexadecimal bytes so invalid UTF-8 and duplicate JSON keys can be represented without the fixture container itself becoming invalid JSON.

The eighteen fixtures cover duplicate keys in policy and request documents, invalid UTF-8, non-standard NaN, unknown request and policy fields, non-object request roots, trailing data, excessive nesting, oversized requests, impossible calendar dates, invalid clock components, and invalid timezone offsets. Each implementation must deny and return the specified reason code. These tests validate parser failure behavior only; they do not prove parser memory safety, exhaustive malformed-input handling, or production security.
