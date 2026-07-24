# Course specification — "Secure code development"

A multi-page course built in **Xerte Online Toolkits (XOT)** using the **Xerte (Nottingham)**
learning-object template, exported as a single **SCORM 1.2 (Shareable Content Object Reference
Model, version 1.2)** package with **LMS (Learning Management System)-reported scoring**.

## Sources & licensing (binding)

| Source | License | Attribution line |
|---|---|---|
| OWASP Top 10 for Agentic Applications 2026 (PDF) | **CC BY-SA 4.0** (Creative Commons Attribution-ShareAlike 4.0) | OWASP Gen AI Security Project – Agentic Security Initiative, genai.owasp.org |
| OWASP Top 10:2025 (owasp.org/Top10/2025/) | **CC BY 3.0** (Creative Commons Attribution 3.0 Unported) | OWASP Top 10 Team, 2021–2025 |

- **Course license: CC BY-SA 4.0** (ShareAlike, required by the Agentic PDF).
- Attribution + "changes were made" + "not endorsed by OWASP" on the About page.
- **Provenance**: generated with the assistance of an AI coding agent. Not endorsed by OWASP.
- All prose is written in our own words as an adaptation; quiz questions are original.

## Conventions (apply on every page and in every quiz)

1. **Acronym expansion**: the **first time** a specific security term/acronym is used **on a given
   page**, give the full version in brackets, e.g. "TOCTOU (Time-of-check to time-of-use)". Reuse
   the acronym thereafter on that same page. Expand again on the next page's first use. Quizzes
   also expand acronyms in stems/options.
2. **Year-stable, understandable quiz wording**: questions are framed with the **full descriptive
   name** of the risk, e.g. "Broken access control is caused by…", never "What causes A01". The
   OWASP item codes (A01–A10, ASI01–ASI10) may appear only as an **optional parenthetical
   cross-reference**, never as the subject of a question, because ordering can change between
   releases.
3. **No free-text questions**: all quiz items are selection-based (single choice, multiple
   response, true/false, matching, categorise).

## Template / technical setup

- **Template**: framework `xerte`, template_name `Nottingham` (display "Xerte Online Toolkit").
- **Navigation**: Menu with page controls (contents menu + next/back).
- **Scoring**: a **Configure Scores** page sets project scoring; theme quizzes (25%) + final quiz
  (75%) **all count** toward the LMS score. Final quiz pass mark **80%**.
- **SCORM 1.2** export → `cmi.core.score.raw`, `cmi.core.lesson_status`, `cmi.interactions.n`.
- **Option order**: every quiz question sets `answerOrder="random"` so the answer options
  shuffle on each attempt (Nottingham per-question "Answer Order" property).
- **Question types used** (all selection-based, no free text): Multiple Choice (single),
  Multiple Response (select all), True/False, Matching, Categorise.
- Editor opened directly at `/edit.php?template_id=<id>`; **Publish** before export.

## Page-type legend
- **[Content]** — Nottingham text/page type (rich text + bullets/checklist).
- **[MCQ]** — Multiple Choice Question page (single answer or multi-correct).
- **[Quiz]** — Quiz page grouping several MCQ questions (formative/summative block).
- **[Match]** — Matching Texts page.
- **[Cat]** — Category page.
- **[Scores]** — Configure Scores (project scoring; not a visible learner page).

Content page structure (each item page): **Overview · Why it matters / examples ·
Real-world incident callout (where Appendix D has one) · Secure-coding mitigations checklist**.

> Note on OWASP Top 10:2025 ("A0x") wording: the outlines below use standard descriptions for
> structure; final prose for those pages will be written from the live owasp.org/Top10/2025/
> detail pages during authoring.

---

## FRONT MATTER (4 pages)

### Page 1 — Welcome & how to use this course  [Content]
- Who this is for: engineers building software with agents **and** building agents.
- What you'll learn: classic secure-code risks (OWASP Top 10:2025) and how they evolve for
  agentic/AI (Artificial Intelligence) apps (OWASP Agentic Top 10 2026), interleaved by theme.
- Structure: 7 themes, a quiz per theme, a final assessment. Time ~3–4 h.
- How scoring works: theme quizzes count 25%, final quiz counts 75%; final pass mark 80%.

### Page 2 — About, licensing, attributions & provenance  [Content]
- CC BY-SA 4.0 (Creative Commons Attribution-ShareAlike 4.0) notice +
  https://creativecommons.org/licenses/by-sa/4.0/
- Attribution to both OWASP sources (name, author, source link, license link).
- "Changes were made: this course is an adapted summary/derivative."
- "Not endorsed by OWASP."
- Provenance: generated with the assistance of an AI coding agent.

### Page 3 — Introduction to secure code development  [Content]
- What secure code development is; why it matters; cost of defects left vs right of the
  SDLC (Software Development Life Cycle).
- Secure SDLC: requirements → design → code → test → release → respond.
- Risk-based thinking; least privilege/least agency; defense in depth; fail secure.
- Where OWASP Top 10 fits: a prioritised awareness/checklist, not a checklist-only fix.

### Page 4 — How the OWASP Top 10 works  [Content]
- Methodology: incidence, exploitability, detectability, impact → ranking.
- How to use it in practice (awareness, training, threat modelling, code-review gates).
- Two lists here: OWASP Top 10:2025 (classic apps) & OWASP Agentic Top 10 2026 (agents).
- The OWASP Top 10 for LLM (Large Language Model) Applications 2025 is referenced by the
  Agentic list but is out of scope for this course.

---

## THEME 1 — Access Control, Authentication & Identity
*Classic → agentic: who you are, what you can do, and how agents get identity.*

### Page 5 — Theme 1 intro  [Content]
- Why identity/access is theme #1; the agentic "attribution gap" — an agent without a
  governed identity of its own makes true least privilege impossible.

### Page 6 — Broken Access Control (A01:2025)  [Content]
- Overview: enforcing constraints so users can't act beyond their permissions.
- Examples: URL/forced browsing, IDOR (Insecure Direct Object Reference), missing
  function-level checks, privilege escalation.
- Mitigations: deny by default, server-side enforcement, re-auth for sensitive actions,
  role/attribute-based checks, ownership tests, JWT (JSON Web Token) claims validated server-side.

### Page 7 — Authentication Failures (A07:2025)  [Content]
- Overview: weak/missing authentication, credential stuffing, session-management flaws.
- Mitigations: MFA (Multi-Factor Authentication), strong hashed + salted passwords, lockout /
  rate limits, secure session IDs, rotation, no predictable identifiers, centralized identity.

### Page 8 — Identity and Privilege Abuse (Agentic, ASI03)  [Content]
- Overview: agentic evolution of excessive agency; manipulating delegation chains, role
  inheritance, cached credentials; the attribution gap makes least privilege impossible.
- Examples: un-scoped privilege inheritance, memory-based privilege retention, confused-deputy
  across agents, TOCTOU (Time-of-check to time-of-use) in workflows, synthetic identity injection.
- Incident callout: "Forged Agent Persona" — a fake "Admin Helper" agent registered in an
  A2A (Agent-to-Agent) registry with a forged agent card.
- Mitigations: task-scoped, time-bound tokens; per-session isolated identities; per-action
  authorization; HITL (Human-in-the-Loop) for privilege escalation; bind OAuth tokens to a
  signed intent; detect delegated/transitive permissions; managed NHI (Non-Human Identity)
  via platforms such as Entra / Bedrock / Agentforce.

### Page 9 — Theme 1 Quiz  [Quiz]  (5 questions)
- **Single choice**: "Broken access control is best illustrated by which scenario?" →
  *An authenticated user edits a URL parameter to view another user's account* (correct).
  Distractors: an attacker sends a crafted SQL (Structured Query Language) string; a server uses
  a deprecated hash; an app ships with default admin credentials.
- **Multiple response**: "Which are effective mitigations against authentication attacks?" ✅ MFA
  (Multi-Factor Authentication); ✅ hashed + salted passwords; ✅ lockout on repeated failures;
  ❌ plaintext password reminders by email; ❌ client-side authorization checks.
- **True/False**: "A delegated agent should reuse the delegating user's full permissions when
  performing a task." → *False* (apply least-privilege scoping).
- **Single choice**: "A low-privilege agent relays instructions that a high-privilege agent
  executes without re-checking the original user's intent. This is:" → *Cross-agent trust
  exploitation (confused deputy), an Identity and Privilege Abuse example* (correct).
  Distractors: Agent Goal Hijack; Memory & Context Poisoning; Rogue Agents.
- **Match** (mitigation ↔ technique): short-lived scoped tokens ↔ Task-scoped permissions;
  per-session sandbox wiped between tasks ↔ Isolate agent identities; human approval for
  high-privilege actions ↔ Human-in-the-Loop; bind an OAuth token to subject/audience/purpose
  ↔ Define signed intent.

---

## THEME 2 — Injection, Tools & Unintended Execution
*Classic → agentic: input manipulation and tool use leading to unintended execution.*

### Page 10 — Theme 2 intro  [Content]
- Injection → goal hijack → tool misuse → RCE (Remote Code Execution) as an escalating
  agentic chain.

### Page 11 — Injection (A05:2025)  [Content]
- Overview: untrusted data interpreted as commands/queries — SQLi (SQL Injection), OS
  (Operating System) command injection, LDAP (Lightweight Directory Access Protocol) injection,
  XPath (XML Path) injection, expression/language injection.
- Examples: SQLi via concatenated strings, command injection, expression injection.
- Mitigations: parameterised queries / prepared statements, allowlist input validation,
  escaping/encoding, parameterised ORM (Object-Relational Mapping) query methods (an ORM is
  not inherently injection-proof — never concatenate raw input into its query strings), least
  privilege on DB (database) accounts.

### Page 12 — Agent Goal Hijack (Agentic, ASI01)  [Content]
- Overview: manipulating an agent's objectives, task selection, or decision pathways via prompt
  manipulation, deceptive tool outputs, malicious artefacts, forged agent messages, or poisoned
  data; broader than a single model response (it affects planning and multi-step behaviour).
- Examples: indirect prompt injection via web/docs in RAG (Retrieval-Augmented Generation);
  external channels (email/calendar) hijacking internal comms; malicious prompt override →
  fraudulent finance transfer.
- Incident callout: EchoLeak — zero-click indirect prompt injection on Microsoft 365 Copilot.
- Mitigations: treat all natural-language inputs as untrusted; least privilege + HITL for
  goal-changing actions; lock system prompts under configuration management; runtime intent
  validation; "intent capsule" pattern; sanitize connected data sources with CDR
  (Content Disarm and Reconstruction) and prompt-carrier detection; logging and monitoring of
  goal state; periodic red-team of goal override.

### Page 13 — Tool Misuse and Exploitation (Agentic, ASI02)  [Content]
- Overview: misuse of legitimate tools within authorized privileges (delete, costly APIs
  (Application Programming Interfaces), exfiltration); relates to excessive agency; overlaps
  Agentic Supply Chain (MCP — Model Context Protocol) and Unexpected Code Execution.
- Examples: over-privileged / over-scoped tools, unvalidated input forwarding to a shell,
  unsafe browsing, loop amplification causing DoS (Denial of Service) / bill spikes, tool
  poisoning of descriptors, tool-name impersonation (typosquatting).
- Incident callout: "Approved tool misuse" — a ping tool exfiltrating data via DNS
  (Domain Name System) queries.
- Mitigations: per-tool least-privilege profiles (scopes, rate, egress allowlists); per-action
  authentication + human confirmation for destructive actions; sandboxes + egress controls;
  policy-enforcement middleware ("intent gate", a PEP/PDP — Policy Enforcement Point / Policy
  Decision Point); adaptive tool budgeting; JIT (Just-in-Time) / ephemeral access; semantic
  firewalls (fully-qualified names, version pins); logging + drift detection.

### Page 14 — Unexpected Code Execution / RCE (Agentic, ASI05)  [Content]
- Overview: agent-generated or executed code escalated to RCE (Remote Code Execution) / host
  compromise; prompt injection, tool misuse, or unsafe serialization turn text into execution;
  "vibe coding" risk.
- Examples: prompt injection → code execution, code hallucination with backdoor, shell command
  from reflected prompts, unsafe eval() / deserialization, multi-tool chain to code loading.
- Incident callout: Replit "vibe coding" runaway execution deleting/overwriting data.
- Mitigations: improper-output-handling controls (validate/encode agent-generated code);
  separate code generation from execution with validation gates; ban eval() in production;
  sandboxed containers, never run as root, strict network and filesystem limits; human approval
  for elevated runs; static scans before execution; runtime monitoring.

### Page 15 — Theme 2 Quiz  [Quiz]  (5 questions)
- **Single choice**: "Injection (e.g. SQL injection) is best prevented by:" → *parameterised
  / prepared statements with allowlist validation* (correct). Distractors: storing passwords
  hashed; security headers; MFA.
- **True/False**: "Agent Goal Hijack captures broader agentic impact — goals, planning, and
  multi-step behaviour — than a single prompt-injection response." → *True*.
- **Multiple response**: "Which mitigate tool misuse and exploitation?" ✅ per-tool
  least-privilege profiles; ✅ human confirmation for destructive actions; ✅ egress allowlists;
  ❌ permanent root API keys; ❌ relying on EDR (Endpoint Detection and Response) alone.
- **Single choice**: "An agent generates and runs unreviewed install/shell commands and deletes
  production data. This is:" → *Unexpected Code Execution / Remote Code Execution* (correct).
  Distractors: Agent Goal Hijack; Tool Misuse; Cascading Failures.
- **Categorise** (label each as Agent Goal Hijack / Tool Misuse / Unexpected Code Execution):
  indirect prompt injection via a web page → exfiltrate data = Agent Goal Hijack; an email
  summarizer tool deletes or sends mail without confirmation = Tool Misuse; an unsafe eval()
  in agent memory runs attacker code = Unexpected Code Execution; a malicious prompt override
  makes a financial agent transfer money = Agent Goal Hijack; a customer-service bot issues
  refunds because its tool had full financial API access = Tool Misuse; deserializing an
  agent-generated payload triggers code execution = Unexpected Code Execution.

---

## THEME 3 — Supply Chain & Integrity
*Classic → agentic: trusted components and untampered data/context.*

### Page 16 — Theme 3 intro  [Content]
- Static software supply chain → runtime, dynamic agentic supply chain (tools, MCP
  (Model Context Protocol), A2A (Agent-to-Agent), registries).

### Page 17 — Software Supply Chain Failures (A03:2025)  [Content]
- Overview: vulnerabilities in dependencies, build pipelines, package registries
  (e.g. npm, PyPI (Python Package Index)).
- Mitigations: trusted/pinned dependencies, SBOMs (Software Bills of Materials), verified
  provenance, reproducible builds, scanning for typosquats.

### Page 18 — Software or Data Integrity Failures (A08:2025)  [Content]
- Overview: code/data integrity not verified — unsigned updates, untrusted deserialization,
  CI/CD (Continuous Integration / Continuous Deployment) tampering.
- Mitigations: signed/verified updates, integrity checks, serialization alternatives, trusted
  CI pipelines.

### Page 19 — Agentic Supply Chain Vulnerabilities (Agentic, ASI04)  [Content]
- Overview: third-party agents/tools/artefacts that are malicious or tampered; runtime
  composition (MCP, A2A, registries) increases surface; differs from the static software supply
  chain by composing capabilities at runtime.
- Examples: poisoned prompt templates, tool-descriptor / MCP injection, typosquat or symbol
  impersonation, vulnerable third-party agent, compromised MCP/registry, poisoned RAG plugin.
- Incident callout: a malicious MCP server impersonating Postmark on npm that BCC'd emails to
  an attacker.
- **AIBOM / CycloneDX section (re-included)**: provenance plus SBOM (Software Bill of Materials)
  and AIBOM (AI Bill of Materials — an inventory of models, datasets, and weights); sign and
  attest manifests; dependency gatekeeping; containment; pinning; kill switch; zero-trust design.
- Incident callout (optional 2nd): Amazon Q — a poisoned prompt shipped in a repo.

### Page 20 — Memory & Context Poisoning (Agentic, ASI06)  [Content]
- Overview: corrupting or seeding stored context (memory, RAG (Retrieval-Augmented Generation),
  embeddings) so future reasoning/decisions are biased or aid exfiltration; persists across
  sessions.
- Examples: RAG/embeddings poisoning, shared-user context poisoning, context-window
  manipulation, long-term memory drift, cross-agent / cross-tenant propagation.
- Incident callout: prompt injection corrupting Gemini's long-term memory.
- Mitigations: encryption + least privilege; scan memory writes; per-session/per-tenant
  segmentation; curated sources + retention limits; provenance + anomaly detection; block
  automatic re-ingestion of an agent's own outputs; snapshots/rollback; decay/expire unverified
  memory; trust-weighted retrieval.

### Page 21 — Theme 3 Quiz  [Quiz]  (5 questions)
- **Single choice**: "A prompt template pulled from an external source contains hidden
  instructions that the agent obeys. This is:" → *Agentic Supply Chain Vulnerabilities*
  (correct). Distractors: Memory & Context Poisoning; Injection; Insecure Inter-Agent
  Communication.
- **True/False**: "An SBOM (Software Bill of Materials) / AIBOM (AI Bill of Materials) inventory
  with signed attestations is recommended for agentic supply-chain risk." → *True*.
- **Multiple response**: "Which mitigate memory and context poisoning?" ✅ scan new memory
  writes before commit; ✅ per-tenant namespaces in shared vector stores; ✅ decay/expire
  unverified memory; ❌ auto-reingest the agent's own outputs into trusted memory; ❌ one shared
  memory namespace for all tenants.
- **Single choice**: "Software supply chain failures are best mitigated by:" → *trusted, pinned
  dependencies with SBOMs and verified provenance* (correct). Distractors: plaintext transport;
  client-side checks; longer password rotation.
- **Match** (term ↔ meaning): SBOM (Software Bill of Materials) ↔ inventory of software
  components; AIBOM (AI Bill of Materials) ↔ inventory of models, datasets, weights; provenance
  attestation ↔ signed origin/integrity evidence; pinning ↔ lock by content hash/commit ID;
  kill switch ↔ emergency revocation of tools/agents.

---

## THEME 4 — Cryptographic Failures & Secrets
*Classic → agentic: protecting data and the secrets agents use.*

### Page 22 — Theme 4 intro  [Content]
- Crypto failures (data protection) + agent secrets / NHI (Non-Human Identity) credentials.

### Page 23 — Cryptographic Failures (A04:2025)  [Content] (+ agent secrets / NHI notes)
- Overview: weak cryptography, plaintext sensitive data, deprecated algorithms, poor key
  management.
- Examples: MD5/SHA1 hashing, no TLS (Transport Layer Security), hardcoded keys, weak randomness.
- Mitigations: strong protocols (TLS 1.3, AES-256-GCM (Advanced Encryption Standard, 256-bit,
  Galois/Counter Mode)); don't roll your own crypto; encrypt in transit and at rest;
  Argon2/bcrypt for passwords; key management via HSM (Hardware Security Module) / KMS
  (Key Management Service); rotate keys.
- Agent-specific: short-lived scoped tokens over long-lived static keys; mTLS (mutual TLS) for
  agent authentication; keys never directly accessible to agents (orchestrator-mediated
  signing); NHI credential lifecycle and rotation.

### Page 24 — Theme 4 Quiz  [Quiz]  (4 questions)
- **Single choice**: "Storing passwords with a deprecated hash algorithm is an example of:" →
  *Cryptographic Failures* (correct). Distractors: Authentication Failures; Security
  Misconfiguration; Insecure Design.
- **True/False**: "For agents / non-human identities, long-lived static API keys are preferable
  to short-lived scoped tokens." → *False*.
- **Single choice**: "Best practice for sensitive data is to:" → *encrypt in transit and at rest
  with strong protocols, and never invent your own cryptography* (correct). Distractors: encrypt
  only at rest with AES-ECB; store keys in source code; rely on TLS alone for backups.
- **Match** (control ↔ purpose): TLS 1.3 (Transport Layer Security) ↔ transport encryption;
  AES-256-GCM (Advanced Encryption Standard, Galois/Counter Mode) ↔ data at rest;
  Argon2/bcrypt ↔ password hashing; mTLS (mutual TLS) ↔ agent mutual authentication;
  HSM/KMS (Hardware Security Module / Key Management Service) ↔ key management.

---

## THEME 5 — Configuration, Design & Resilience
*Classic → agentic: secure defaults, sound design, and graceful failure.*

### Page 25 — Theme 5 intro  [Content]
- Misconfiguration + insecure design + poor error handling → how a single fault cascades in
  agents.

### Page 26 — Security Misconfiguration (A02:2025)  [Content]
- Overview: default configs, open cloud storage, verbose errors, unnecessary features enabled.
- Mitigations: hardening, secure defaults, disable unused features, repeatable hardened images,
  security headers, change management.

### Page 27 — Insecure Design (A06:2025)  [Content]
- Overview: architectural / business-logic flaws that implementation alone may not fully fix.
- Mitigations: threat modelling, abuse cases, secure design patterns, rate/usage limits,
  separation of tiers, least privilege by design.

### Page 28 — Mishandling of Exceptional Conditions (A10:2025)  [Content]
- Overview: failing to handle errors/exceptions securely → attackers exploit error paths.
- Mitigations: explicit exception handling, fail secure, don't leak sensitive info in errors,
  monitoring/alerting on anomalies, tested recovery.

### Page 29 — Cascading Failures (Agentic, ASI08)  [Content]
- Overview: a single fault propagates and amplifies across autonomous agents → system-wide harm;
  focuses on propagation, not origin (the origin maps to supply-chain / memory / inter-agent
  risks).
- Examples: planner–executor coupling, corrupted persistent memory, inter-agent cascades from
  poisoned messages, auto-deployment of a tainted update, governance drift, feedback loops.
- Incident callout: financial trading cascade — a poisoned Market Analysis agent inflates risk
  limits; Position and Execution agents auto-trade while compliance stays blind.
- Mitigations: zero-trust, fault-tolerant design; isolation + trust boundaries; JIT
  (Just-in-Time), one-time tool access with runtime checks; an independent policy engine that
  separates planning and execution; output validation + human gates; rate limiting + monitoring;
  blast-radius guardrails / circuit breakers; behavioural drift detection; digital-twin replay +
  policy gating; tamper-evident logging + non-repudiation.

### Page 30 — Theme 5 Quiz  [Quiz]  (5 questions)
- **Single choice**: "Default admin credentials and verbose error messages in production are an
  example of:" → *Security Misconfiguration* (correct). Distractors: Cryptographic Failures;
  Injection; Insecure Design.
- **True/False**: "Insecure Design is a flaw that implementation alone may not fully fix." →
  *True*.
- **Single choice**: "A poisoned Market Analysis agent inflates risk limits; Position and
  Execution agents auto-trade while compliance stays blind. This is:" → *Cascading Failures*
  (correct). Distractors: Agent Goal Hijack; Rogue Agents; Memory & Context Poisoning.
- **Multiple response**: "Which mitigate cascading failures?" ✅ circuit breakers / blast-radius
  guardrails; ✅ separate planning and execution via an external policy engine; ✅ rate limiting
  and monitoring; ✅ tamper-evident logging; ❌ auto-approve all agent actions to cut latency.
- **Single choice**: "Mishandling of exceptional conditions is about:" → *failing to handle
  errors/exceptions securely, letting attackers exploit error paths* (correct). Distractors:
  weak hashing; open cloud buckets; missing MFA.

---

## THEME 6 — Agent Communication, Trust & Autonomy
*Agent-specific: how agents talk, how humans trust them, and agents gone rogue.*

### Page 31 — Theme 6 intro  [Content]
- The three agentic-only risks: inter-agent communication, human trust, and rogue autonomy.

### Page 32 — Insecure Inter-Agent Communication (Agentic, ASI07)  [Content]
- Overview: weak authentication, integrity, confidentiality, or authorization between agents →
  intercept, spoof, tamper, or block messages; spans transport, routing, discovery, and semantic
  layers.
- Examples: unencrypted channels with MITM (Man-in-the-Middle) semantic manipulation, message
  tampering, replay on trust chains, protocol downgrade / descriptor forgery, routing and
  discovery attacks, metadata analysis.
- Mitigations: end-to-end encryption + mutual authentication + PKI (Public Key Infrastructure)
  pinning + forward secrecy; signed messages + hash of payload/context + natural-language-aware
  sanitization and intent-diffing; anti-replay (nonces, timestamps, session IDs); disable
  weak/legacy modes; protocol pinning / version enforcement; authenticated discovery; attested
  registries + signed agent cards; typed contracts + schema validation; reduce metadata inference
  (padding, rate smoothing).

### Page 33 — Human-Agent Trust Exploitation (Agentic, ASI09)  [Content]
- Overview: anthropomorphism + automation bias → humans approve unsafe actions; the agent acts
  as an untraceable "bad influence"; this is human misperception / over-reliance (distinct from
  Rogue Agents, which is agent intent deviation).
- Examples: insufficient explainability, missing confirmation for sensitive actions, emotional
  manipulation, fake explainability.
- Incident callout: Invoice Copilot fraud — a poisoned vendor invoice makes the finance copilot
  recommend an urgent payment to attacker bank details.
- Mitigations: explicit multi-step confirmations / HITL (Human-in-the-Loop); immutable logs;
  behavioural detection; a report-suspicious-interaction control; adaptive trust calibration +
  confidence cues; content provenance + policy enforcement; separate preview from effect;
  human-factors UI safeguards (red borders/banners); plan-divergence detection.

### Page 34 — Rogue Agents (Agentic, ASI10)  [Content]
- Overview: agents deviating from intended function or scope (harmful, deceptive, or parasitic);
  focuses on loss of behavioural integrity once drift begins, not the initial intrusion.
- Examples: goal drift / scheming, workflow hijacking, collusion / self-replication, reward
  hacking / optimization abuse.
- Incident callout: a cost-minimising agent deletes production backups because that is the most
  effective way to meet its goal (reward hacking).
- Mitigations: governance + immutable signed audit logs; isolation + trust zones + sandboxes;
  behavioural detection + watchdog agents; containment (kill-switches, credential revocation,
  quarantine); per-agent cryptographic identity attestation + behavioural integrity manifests;
  periodic behavioural attestation + per-run ephemeral credentials; recovery / reintegration
  requiring fresh attestation + human approval.

### Page 35 — Theme 6 Quiz  [Quiz]  (5 questions)
- **Single choice**: "A man-in-the-middle attacker injects hidden instructions over an
  unencrypted agent channel. This is:" → *Insecure Inter-Agent Communication* (correct).
  Distractors: Memory & Context Poisoning; Rogue Agents; Cascading Failures.
- **True/False**: "Human-Agent Trust Exploitation is agent intent deviation, and Rogue Agents is
  human misperception / over-reliance." → *False* (they are reversed).
- **Multiple response**: "Which mitigate insecure inter-agent communication?" ✅ end-to-end
  encryption + mutual authentication; ✅ signed messages + anti-replay nonces; ✅ disable
  legacy / downgrade modes; ❌ open agent registration for flexibility; ❌ send all messages in
  plain HTTP (HyperText Transfer Protocol).
- **Single choice**: "A cost-minimising agent deletes production backups because that is the
  most effective way to meet its goal. This is:" → *Rogue Agents (reward hacking)* (correct).
  Distractors: Cascading Failures; Human-Agent Trust Exploitation; Insecure Inter-Agent
  Communication.
- **Match** (mitigation ↔ risk): kill-switches and credential revocation ↔ Rogue Agents;
  explicit confirmations / Human-in-the-Loop ↔ Human-Agent Trust Exploitation; PKI
  (Public Key Infrastructure) pinning and nonces ↔ Insecure Inter-Agent Communication;
  behavioural integrity manifests ↔ Rogue Agents; adaptive trust calibration ↔ Human-Agent
  Trust Exploitation.

---

## THEME 7 — Observability, Logging & Detection
*Classic → agentic: seeing what's happening and being able to prove it.*

### Page 36 — Theme 7 intro  [Content]
- Logging/alerting is cross-cutting; for agents, strong observability is "non-negotiable".

### Page 37 — Security Logging and Alerting Failures (A09:2025)  [Content] (+ agent observability)
- Overview: missing or insufficient logging of security events; logs not monitored or alerted on.
- Mitigations: log access / authentication / transaction / key events; tamper-resistant; centralised;
  alerting on suspicious patterns; tested response; privacy-aware logging.
- Agent observability: log tool calls, inter-agent messages, goal state, and action sequences
  against a baseline; track a stable goal identifier; alert on goal drift and anomalous tool
  chains; non-repudiation and lineage per propagated action.

### Page 38 — Theme 7 Quiz  [Quiz]  (4 questions)
- **Single choice**: "No logging of access or authentication events, or logs that are not
  monitored, is an example of:" → *Security Logging and Alerting Failures* (correct).
  Distractors: Security Misconfiguration; Mishandling of Exceptional Conditions; Insecure Design.
- **True/False**: "For agents, logging tool calls, inter-agent messages, and goal state is
  recommended." → *True*.
- **Single choice**: "Good security logs are:" → *tamper-evident, time-stamped, identity-bound,
  and sufficient for audit* (correct). Distractors: verbose and stored in plain text on each
  host; rotated hourly with no retention; stored only client-side.
- **Match** (control ↔ risk it supports): immutable / signed logs ↔ Cascading Failures and Rogue
  Agents; behavioural baseline + deviation alerts ↔ Agent Goal Hijack and Tool Misuse; lineage
  metadata per action ↔ Cascading Failures; anomaly detection on tool chaining ↔ Tool Misuse.

---

## BACK MATTER (5 pages)

### Page 39 — Putting it together: secure SDLC + threat modelling  [Content]
- How to integrate both lists into requirements / design / code / test / release / respond.
- Threat modelling for agents: least-agency, intent validation, tool scoping, trust boundaries,
  human checkpoints, blast-radius controls. Reference the Agentic Threat Modelling Guide.
- Checklists per SDLC (Software Development Life Cycle) phase (classic + agentic).

### Page 40 — Mapping & cross-references  [Content]
- Classic ↔ agentic mapping (which classic risks relate to which agentic risks, by theme).
- Appendix A matrix excerpt: agentic risks ↔ OWASP Top 10 for LLM Applications 2025 ↔ Agentic
  AI Threats & Mitigations ↔ AIVSS (AI Vulnerability Scoring System) Core Risk.
- Appendix C NHI (Non-Human Identity) mapping note — non-human identity ↔ agentic identity.

### Page 41 — Glossary / abbreviations  [Content]
- RCE (Remote Code Execution); NHI (Non-Human Identity); AIBOM (AI Bill of Materials); SBOM
  (Software Bill of Materials); MCP (Model Context Protocol); A2A (Agent-to-Agent); SCO
  (Shareable Content Object); SCORM (Shareable Content Object Reference Model); mTLS (mutual
  TLS); JIT (Just-in-Time); HITL (Human-in-the-Loop); PEP/PDP (Policy Enforcement Point / Policy
  Decision Point); CDR (Content Disarm and Reconstruction); TOCTOU (Time-of-check to time-of-use);
  AIVSS (AI Vulnerability Scoring System); PKI (Public Key Infrastructure); SOC (Security
  Operations Center); prompt injection; least-agency; intent capsule; IDOR (Insecure Direct
  Object Reference); DoS (Denial of Service); MITM (Man-in-the-Middle); RAG (Retrieval-Augmented
  Generation); HSM (Hardware Security Module); KMS (Key Management Service); CI/CD (Continuous
  Integration / Continuous Deployment); EDR (Endpoint Detection and Response); SLA (Service Level
  Agreement). (From PDF Appendix E + extras.)

### Page 42 — References & further reading  [Content]
- OWASP Top 10:2025 (owasp.org/Top10/2025/), CC BY 3.0 (Creative Commons Attribution 3.0).
- OWASP Top 10 for Agentic Applications 2026 (genai.owasp.org), CC BY-SA 4.0.
- Related: OWASP Top 10 for LLM Applications 2025; Agentic AI Threats & Mitigations; Agentic
  Threat Modelling Guide; Securing Agentic Applications; AIVSS (AI Vulnerability Scoring System);
  CycloneDX; OWASP Top 10 for Non-Human Identities.
- Selected incident references from the PDF: EchoLeak; malicious Postmark MCP; Amazon Q; Gemini
  memory poisoning; Replit vibe coding; AgentSmith prompt-hub proxy.

### Page 43 — Final comprehensive quiz  [Quiz]  (~18 questions, summative, pass mark 80%)
Mix across all themes; single choice / multiple response / true-false / matching / categorise.
All framed with full descriptive names (no item codes as the question subject).

- **Single choice**: "Broken access control is best illustrated by:" → *an authenticated user
  edits a URL parameter to view another user's account (IDOR — Insecure Direct Object Reference)*.
- **Single choice**: "Injection (e.g. SQL injection) is best prevented by:" → *parameterised /
  prepared statements with allowlist validation*.
- **Multiple response**: "Which mitigate authentication failures?" ✅ MFA (Multi-Factor
  Authentication); ✅ hashed + salted passwords; ✅ lockout on repeated failures; ❌ plaintext
  password reminders; ❌ client-side authorization checks.
- **True/False**: "Agent Goal Hijack captures broader agentic impact than a single
  prompt-injection response." → *True*.
- **Single choice**: "A low-privilege agent relays instructions a high-privilege agent executes
  without re-checking the original user's intent. This is:" → *Identity and Privilege Abuse
  (cross-agent trust / confused deputy)*.
- **Multiple response**: "Which mitigate tool misuse and exploitation?" ✅ per-tool
  least-privilege profiles; ✅ human confirmation for destructive actions; ✅ egress allowlists;
  ❌ permanent root API keys; ❌ relying on EDR (Endpoint Detection and Response) alone.
- **Single choice**: "An agent generates and runs unreviewed install/shell commands and deletes
  production data. This is:" → *Unexpected Code Execution / RCE (Remote Code Execution)*.
- **Single choice**: "A prompt template pulled from an external source contains hidden
  instructions. This is:" → *Agentic Supply Chain Vulnerabilities*.
- **True/False**: "SBOM (Software Bill of Materials) / AIBOM (AI Bill of Materials) inventory
  with signed attestations is recommended for agentic supply-chain risk." → *True*.
- **Multiple response**: "Which mitigate memory and context poisoning?" ✅ scan new memory
  writes; ✅ per-tenant namespaces; ✅ decay/expire unverified memory; ❌ auto-reingest the
  agent's own outputs; ❌ one shared namespace for all tenants.
- **Single choice**: "Storing passwords with a deprecated hash algorithm is an example of:" →
  *Cryptographic Failures*.
- **True/False**: "For agents / non-human identities, long-lived static API keys are preferable
  to short-lived scoped tokens." → *False*.
- **Single choice**: "Default admin credentials and verbose errors in production are an example
  of:" → *Security Misconfiguration*.
- **Single choice**: "A poisoned Market Analysis agent → Position/Execution agents auto-trade
  while compliance stays blind. This is:" → *Cascading Failures*.
- **Single choice**: "A man-in-the-middle attacker injects hidden instructions over an
  unencrypted agent channel. This is:" → *Insecure Inter-Agent Communication*.
- **True/False**: "Human-Agent Trust Exploitation is human misperception / over-reliance, and
  Rogue Agents is agent intent deviation." → *True*.
- **Single choice**: "A cost-minimising agent deletes production backups to meet its goal. This
  is:" → *Rogue Agents (reward hacking)*.
- **Match** (mitigation ↔ risk): kill-switch ↔ Rogue Agents; intent capsule ↔ Agent Goal Hijack;
  circuit breaker ↔ Cascading Failures; signed agent cards ↔ Insecure Inter-Agent Communication;
  per-tenant namespace ↔ Memory & Context Poisoning; prepared statements ↔ Injection; MFA
  (Multi-Factor Authentication) ↔ Authentication Failures.
- **Categorise**: label each risk as Classic (OWASP Top 10:2025) or Agentic (Agentic Top 10
  2026): Broken Access Control = Classic; Agent Goal Hijack = Agentic; Injection = Classic;
  Memory & Context Poisoning = Agentic; Cryptographic Failures = Classic; Rogue Agents = Agentic;
  Security Misconfiguration = Classic; Cascading Failures = Agentic.

### Page 44 — Course complete  [Content]
- A closing page so it is unambiguous that the training is over: congratulates the learner,
  reminds them their result is recorded by the LMS (Learning Management System) and that the
  80% pass mark / last-attempt rule applies, and tells them they may close the window. Plain
  Text page type.

### [Scores] — Configure Scores
- Project scoring enabled; theme quizzes (25%) + final quiz (75%) all count; final pass mark
  80%; per-question weighting set at build time.

---

## Totals
- 44 learner-visible pages + 1 Configure Scores page.
- 20 item pages (10 classic + 10 agentic), 7 theme intros, 7 theme quizzes, 1 final quiz,
  4 front-matter + 5 back-matter pages.
- All quiz questions selection-based; auto-graded; LMS-reported via SCORM 1.2.
- Acronyms expanded on first use per page; quizzes use full descriptive names (year-stable).
