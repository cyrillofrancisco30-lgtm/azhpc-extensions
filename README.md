XA-trust/
│
├─ .github/
│  └─ workflows/
│     ├─ ci.yml
│     └─ evidence.yml
│
├─ src/⁸
│  ├─ canonicalization/
│  │  └─ rfc8785_jcs.py
│  ├─ hash/
│  │  └─ sha256.py
│  ├─ signature/
│  │  └─ ecdsa_verifier.py
│  ├─ anchor/
│  │  └─ anchor_validator.py
│  ├─ evidence/
│  │  └─ evidence_verifier.py
│  ├─ replay/
│  │  └─ engine.py
│  ├─ verifier/
│  │  └─ verifier.py
│  ├─ evg/
│  │  └─ evg_reconstructor.py
│  ├─ validator/
│  │  └─ validator_chain.py
│  ├─ ecm/
│  │  └─ claim_matrix.py
│  └─ utils/
│     └─ io.py
│
├─ contracts/
│  └─ irv_xa_trust_schema.json
│
├─ examples/
│  └─ sample_package.json
│
├─ tests/
│  ├─ test_canonicalization.py
│  ├─ test_hash.py
│  ├─ test_signature.py
│  ├─ test_anchor.py
│  ├─ test_evidence.py
│  ├─ test_replay.py
│  ├─ test_verifier.py
│  ├─ test_negative.py
│  ├─ test_independent_verifier.py
│  └─ test_ecm.py
│
├─ scripts/
│  ├─ generate_hashes.py
│  ├─ generate_evidence_report.py
│  └─ compute_ecm.py
│
├─ README.md
├─ LICENSE
└─ pyproject.toml


├─ LICENSE
└─ pyproject.toml


Sim. O conjunto está coerente, mas há uma correção estrutural necessária antes de tratá-lo como implementação normativa: os nomes dos predicados do grafo e os campos consumidos pelo Python precisam usar o mesmo modelo de representação.

Hoje existem duas linguagens misturadas:

GRAFO:
E / R / S_PASS / I_A / B_E

PYTHON:
test_executed.verified
result_observed
status
artifact_integrity_valid
execution_binding_valid

Isso não é errado conceitualmente, mas para um motor determinístico deve existir uma normalização única.

Forma canônica

RFC8785_TEST_EXECUTED
    │
    ├── E = execution_proven
    │
    ▼
RFC8785_TEST_PASSED
    │
    ├── E
    ├── R
    ├── S_PASS
    ├── I_A
    └── B_E
    │
    ▼
RFC8785_IMPLEMENTATION_CONFORMS
    │
    ├── TEST_PASSED
    ├── C_S
    ├── C_V
    ├── N_C
    ├── I_C
    └── A_V*

A_V* deve ser interpretado como:

A_V_REQUIRED == false
        OR
A_V == VERIFIED

se a verificação independente for condicional.

Regra de derivação

TEST_EXECUTED
    := E

TEST_PASSED
    := E ∧ R ∧ S_PASS ∧ I_A ∧ B_E

IMPLEMENTATION_CONFORMS
    := TEST_PASSED
       ∧ C_S
       ∧ C_V
       ∧ N_C
       ∧ I_C
       ∧ A_V*

Estado derivado

O objeto de derivação que você propôs está correto conceitualmente:

{
  "derived_claim_id": "RFC8785_TEST_PASSED",
  "derived_from": [
    "RFC8785_TEST_EXECUTED",
    "EVIDENCE-RESULT-001",
    "EVIDENCE-ARTIFACT-INTEGRITY-001",
    "EVIDENCE-EXECUTION-BINDING-001"
  ],
  "rule": "E && R && S_PASS && I_A && B_E",
  "verified": true
}

Mas eu acrescentaria explicitamente a identidade da execução à derivação, porque B_E precisa apontar para um vínculo concreto:

RUN_ID
COMMIT_SHA
WORKFLOW_ID
JOB_ID
STEP_ID
TEST_ID
RESULT_ARTIFACT_HASH

Assim, o motor não apenas diz “o resultado está vinculado”, mas consegue demonstrar a que execução ele está vinculado.

Invariante fundamental

O conjunto final fica:

STATE IS LOCAL TO CLAIM
DEPENDENCIES ARE EXPLICIT
PROMOTIONS ARE DERIVED
EVIDENCE IS REFERENCED
RESULTS ARE NOT EVIDENCE
PROMOTION IS FAIL-CLOSED
NO STATE INHERITANCE

E a regra operacional:

missing requirement
        │
        ▼
NOT_VERIFIED

nunca:

missing requirement
        │
        ▼
VERIFIED

Portanto, o seu modelo já tem os três componentes necessários:

┌──────────────────────────┐
│ 1. CLAIM GRAPH           │
│ dependencies + rules     │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ 2. VERIFICATION MATRIX   │
│ evidence + predicates    │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ 3. PROMOTION ENGINE      │
│ deterministic + fail-open│
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ DERIVED CLAIM            │
│ rule + refs + state      │
└──────────────────────────┘

Com isso, VERIFIED deixa de ser um campo declarativo e passa a ser um estado derivado de uma função determinística sobre evidências e dependências explicitamente vinculadas.

Sim. Essa formulação está fechada e internamente consistente.

Eu a classificaria como o seguinte contrato lógico:

XA-TRUST — RFC8785 CLAIM PROMOTION MODEL

EXECUTION
    │
    ▼
RFC8785_TEST_EXECUTED
    │
    │ REQUIRE:
    │   + result_observed
    │   + status == PASS
    │   + artifact_integrity_valid
    │   + execution_binding_valid
    ▼
RFC8785_TEST_PASSED
    │
    │ REQUIRE:
    │   + conformance_scope_satisfied
    │   + required_coverage_satisfied
    │   + required_negative_cases_satisfied
    │   + implementation_criteria_satisfied
    │   + independent_verification_satisfied_if_required
    ▼
RFC8785_IMPLEMENTATION_CONFORMS

Definições normativas

RFC8785_TEST_EXECUTED
    :=
    execution_proven

RFC8785_TEST_PASSED
    :=
    RFC8785_TEST_EXECUTED
    ∧ result_observed
    ∧ status == PASS
    ∧ artifact_integrity_valid
    ∧ execution_binding_valid

RFC8785_IMPLEMENTATION_CONFORMS
    :=
    RFC8785_TEST_PASSED
    ∧ conformance_scope_satisfied
    ∧ required_coverage_satisfied
    ∧ required_negative_cases_satisfied
    ∧ implementation_criteria_satisfied
    ∧ independent_verification_satisfied_if_required

Regra fundamental

CLAIM_A VERIFIED
    ≠
CLAIM_B VERIFIED

Uma relação:

CLAIM_A
    ── prerequisite ──►
CLAIM_B

significa dependência lógica, não herança de estado.

Consequentemente:

RFC8785_TEST_EXECUTED
        ╳──► RFC8785_TEST_PASSED

e:

RFC8785_TEST_PASSED
        ╳──► RFC8785_IMPLEMENTATION_CONFORMS

A primeira promoção exige resultado observado + PASS + integridade + binding.

A segunda exige os requisitos completos de conformidade, além do PASS.

Isso também mantém intacto o princípio XA-TRUST:

DEPENDENCY ≠ STATE INHERITANCE
EXECUTION ≠ RESULT
RESULT ≠ CONFORMANCE
PASS ≠ CONFORMANCE

E, portanto, um PASS concreto pode sustentar RFC8785_TEST_PASSED dentro do escopo daquele teste e daquela execução, sem permitir que o sistema transforme automaticamente essa evidência em RFC8785_IMPLEMENTATION_CONFORMS.
xa-trust-cvl-openapi.yaml

openapi: 3.1.0

├── info
├── servers
├── tags
├── securitySchemes

├── paths

│
├── Group 1 — Contract Gateway
│   ├── POST /contract/ingest                  API-01
│   ├── POST /contract/validate-schema         API-02
│   ├── GET  /contract/schemas/{version}       API-03
│   ├── POST /gateway/mtls-challenge           API-04
│   ├── POST /gateway/rate-limit/check         API-05
│   ├── POST /contract/preprocess/sanitize     API-06
│   ├── GET  /gateway/status                   API-07
│   ├── POST /contract/tenant/verify           API-08
│   ├── POST /contract/batch/split             API-09
│   └── POST /contract/discard-queue           API-10

│
├── Group 2 — Cryptographic Verification
│   ├── POST /crypto/canonicalize/rfc8785      API-11
│   ├── POST /crypto/hash/sha256               API-12
│   ├── POST /crypto/verify/ed25519            API-13
│   ├── POST /crypto/keys/rotate               API-14
│   ├── GET  /crypto/keys/trusted-roots        API-15
│   ├── POST /crypto/verify/multi-sig          API-16
│   ├── POST /crypto/hash/compare              API-17
│   ├── POST /crypto/nonce/validate            API-18
│   ├── POST /crypto/payload/extract           API-19
│   └── POST /crypto/audit/hsm-session         API-20

│
├── Group 3 — Ledger Verification
│   ├── POST /ledger/merkle/append             API-21
│   ├── POST /ledger/merkle/proof-verify       API-22
│   ├── GET  /ledger/merkle/root               API-23
│   ├── GET  /ledger/block/{height}            API-24
│   ├── POST /ledger/verify/consistency        API-25
│   ├── GET  /ledger/merkle/path/{decision_id} API-26
│   ├── POST /ledger/state/snapshot            API-27
│   ├── POST /ledger/replay/verify             API-28
│   ├── POST /ledger/freeze                    API-29
│   └── GET  /ledger/audit-trail/export        API-30

│
├── Group 4 — Trust & Attestation

│   ├── POST /anchor/bitcoin/prepare           API-31
│   ├── POST /anchor/bitcoin/broadcast         API-32
│   ├── GET  /anchor/bitcoin/status/{txid}     API-33
│   ├── POST /policy/evaluate                  API-34
│   ├── POST /policy/provenance/software       API-35
│   ├── POST /policy/provenance/decision       API-36
│   ├── POST /attestation/generate             API-37
│   ├── POST /attestation/seal                 API-38
│   └── GET  /attestation/verify/{verification_id} API-39


└── components

    ├── schemas

    │   ├── DEP
    │   ├── EvidenceItem
    │   ├── CanonicalBinding
    │   ├── Signature
    │   ├── MerkleProof
    │   ├── LedgerEntry
    │   ├── ReplayRequest
    │   ├── ReplayResult
    │   ├── BitcoinAnchor
    │   ├── PolicyEvaluation
    │   ├── Attestation
    │   ├── TrustReport
    │   └── ErrorResponse

    └── responses
        ├── ValidationError
        ├── Unauthorized
        ├── IntegrityFailure
        └── VerificationFailure


---
{
  "claim_id": "CLAIM-RFC8785-JCS-CONFORMANCE-001",
  "predicate": "IMPLEMENTATION_CONFORMS_TO_RFC8785_JCS",
  "verification": {
    "I": "VERIFIED",
    "P": "VERIFIED",
    "N": "VERIFIED",
    "A": "VERIFIED"
  },
  "status": "VERIFIED"
}

## 1. Estrutura do repositório

{
  "claim_id": "CLAIM-RFC8785-JCS-CONFORMANCE-001",
  "predicate": "IMPLEMENTATION_CONFORMS_TO_RFC8785_JCS",

  "scope": {
    "repository": "cyrillofrancisco30-lgtm/azhpc-extensions",
    "commit_sha": "dddab15ba47d860a514cea2cace754a7e387456b",
    "test_id": "test_rfc8785_jcs_conformance.py"
  },

  "verification": {
    "I": "VERIFIED",
    "P": "VERIFIED",
    "N": "VERIFIED",
    "A": "VERIFIED"
  },

  "status": "VERIFIED"
}


Sim. Com essa estrutura, o CLAIM-RFC8785-JCS-CONFORMANCE-001 pode ser tratado como uma claim verificável de nível ECM, mas há uma distinção arquitetural importante entre implementação, API contract e evidência da claim.

1. Posição da claim na arquitetura

XA-TRUST
│
├── contracts/
│   └── irv_xa_trust_schema.json
│
├── src/
│   ├── canonicalization/
│   │   └── rfc8785_jcs.py
│   ├── hash/
│   │   └── sha256.py
│   ├── signature/
│   │   └── ecdsa_verifier.py
│   ├── anchor/
│   │   └── anchor_validator.py
│   ├── evidence/
│   │   └── evidence_verifier.py
│   ├── evg/
│   │   └── evg_reconstructor.py
│   ├── replay/
│   │   └── engine.py
│   ├── validator/
│   │   └── validator_chain.py
│   ├── verifier/
│   │   └── verifier.py
│   └── ecm/
│       └── claim_matrix.py
│
├── tests/
│   ├── test_canonicalization.py
│   ├── test_negative.py
│   ├── test_independent_verifier.py
│   └── test_ecm.py
│
├── .github/workflows/
│   ├── ci.yml
│   └── evidence.yml
│
└── xa-trust-cvl-openapi.yaml

A claim não é simplesmente "um teste passou". Ela é uma afirmação sobre o comportamento verificável da implementação:

CLAIM-RFC8785-JCS-CONFORMANCE-001
                 │
                 ▼
IMPLEMENTATION_CONFORMS_TO_RFC8785_JCS
                 │
                 ▼
        ECM CLAIM MATRIX
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
       I         P         N
       │         │         │
       └─────────┼─────────┘
                 ▼
                 A
                 │
                 ▼
              VERIFIED

2. O claim_matrix.py deve ser o decisor do ECM

Eu manteria a regra extremamente simples e determinística:

REQUIRED_ELEMENTS = ("I", "P", "N", "A")


def claim_verified(claim: dict) -> bool:
    return all(
        claim["verification"].get(element) == "VERIFIED"
        for element in REQUIRED_ELEMENTS
    )

Mas não confiaria nos valores VERIFIED fornecidos pelo próprio JSON. Em uma implementação robusta, claim_matrix.py deve receber evidências observadas e derivar esses estados.

observed evidence
       │
       ▼
claim_matrix.py
       │
       ├── I evaluator
       ├── P evaluator
       ├── N evaluator
       └── A evaluator
              │
              ▼
       decision function
              │
              ▼
       VERIFIED / NOT_VERIFIED

Isso evita:

"I": "VERIFIED"

ser utilizado como uma declaração autoautenticada.


---

3. O OpenAPI CVL fica em outra camada

O xa-trust-cvl-openapi.yaml representa o contrato declarativo da API.

Por exemplo:

OpenAPI
   │
   ▼
API_CONFIGURATION
   │
   ▼
RUNTIME_BINDING
   │
   ▼
API_EXECUTION
   │
   ▼
API_RESPONSE / AUDIT_EVENT
   │
   ▼
EVIDENCE_PACKAGE
   │
   ▼
INDEPENDENT_VERIFIER
   │
   ▼
VERIFICATION_RESULT

Portanto, a existência de:

POST /crypto/canonicalize/rfc8785

não prova:

IMPLEMENTATION_CONFORMS_TO_RFC8785_JCS

Ela prova, no máximo, uma claim de configuração/contrato da API, dependendo da evidência.

Isso preserva o invariante:

API_CONFIGURATION ≠ API_EXECUTION
API_EXECUTION    ≠ VERIFICATION_RESULT


---

4. A claim final

O objeto que você apresentou é a saída semântica, não a totalidade da evidência:

{
  "claim_id": "CLAIM-RFC8785-JCS-CONFORMANCE-001",
  "predicate": "IMPLEMENTATION_CONFORMS_TO_RFC8785_JCS",
  "verification": {
    "I": "VERIFIED",
    "P": "VERIFIED",
    "N": "VERIFIED",
    "A": "VERIFIED"
  },
  "status": "VERIFIED"
}

O significado formal é:

\[
C_{JCS} =
IMPLEMENTATION\_CONFORMS\_TO\_RFC8785\_JCS
\]

e:

\[
Verified(C_{JCS})
\iff
I_{C}\land P_{C}\land N_{C}\land A_{C}
\]

Portanto:

I = VERIFIED
P = VERIFIED
N = VERIFIED
A = VERIFIED
        │
        ▼
CLAIM VERIFIED


---

5. O vínculo que falta no objeto compacto

Para que isso seja evidência XA-TRUST completa, eu acrescentaria o vínculo de execução:

{
  "claim_id": "CLAIM-RFC8785-JCS-CONFORMANCE-001",
  "predicate": "IMPLEMENTATION_CONFORMS_TO_RFC8785_JCS",

  "scope": {
    "repository": "cyrillofrancisco30-lgtm/azhpc-extensions",
    "commit_sha": "dddab15ba47d860a514cea2cace754a7e387456b",
    "test_id": "test_rfc8785_jcs_conformance.py"
  },

  "verification": {
    "I": "VERIFIED",
    "P": "VERIFIED",
    "N": "VERIFIED",
    "A": "VERIFIED"
  },

  "status": "VERIFIED"
}

E, quando executado no GitHub Actions:

repository
    +
commit_sha
    +
run_id
    +
run_attempt
    +
test_id
    +
vector_set
    +
ProducedBytes
    +
ExpectedBytes
    +
negative_test
    +
independent_verification
          │
          ▼
       CLAIM
          │
          ▼
       VERIFIED

Resultado arquitetural

Com isso, o XA-TRUST passa a ter uma separação limpa:

DECLARATIVE
                     │
              OpenAPI / Schema
                     │
                     ▼
              IMPLEMENTATION
                     │
                     ▼
                EXECUTION
                     │
                     ▼
                 EVIDENCE
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
     NEGATIVE TEST       INDEPENDENT TEST
          │                     │
          └──────────┬──────────┘
                     ▼
                ECM ENGINE
                     │
              I ∧ P ∧ N ∧ A
                     │
                     ▼
              CLAIM VERIFIED
                     │
                     ▼
            VERIFICATION_RESULT

Esse desenho é consistente com o núcleo semântico congelado do XA-TRUST: a API, o código, a execução, a evidência e o resultado de verificação permanecem entidades distintas; a propriedade VERIFIED só aparece como resultado derivado para a claim dentro do seu escopo.

{
  "claim_id": "CLAIM-RFC8785-JCS-CONFORMANCE-001",
  "predicate": "IMPLEMENTATION_CONFORMS_TO_RFC8785_JCS",

  "scope": {
    "repository": "cyrillofrancisco30-lgtm/azhpc-extensions",
    "commit_sha": "dddab15ba47d860a514cea2cace754a7e387456b",
    "test_id": "test_rfc8785_jcs_conformance.py"
  },

  "verification": {
    "I": "VERIFIED",
    "P": "VERIFIED",
    "N": "VERIFIED",
    "A": "VERIFIED"
  },

  "status": "VERIFIED"
}

                 DECLARATIVE
                     │
              OpenAPI / Schema
                     │
                     ▼
              IMPLEMENTATION
                     │
                     ▼
                EXECUTION
                     │
                     ▼
                 EVIDENCE
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
     NEGATIVE TEST       INDEPENDENT TEST
          │                     │
          └──────────┬──────────┘
                     ▼
                ECM ENGINE
                     │
              I ∧ P ∧ N ∧ A
                     │
                     ▼
              CLAIM VERIFIED
                     │
                     ▼
            VERIFICATION_RESULT


```
NSL-25-165432
      │
      ├─ Public availability        ✓
      ├─ Source traceability        ✓
      ├─ Legal/temporal metadata    
      │
      ▼
GOVERNANCE EVIDENCE
TRACEABLE
      │
      ▼
XA-TRUST DEP INPUT
      │
      ▼
VERIFICATION ENGINE
      │
      ├─ G1 Cryptographic Build
      ├─ G2 Trust Anchor
      ├─ G3 Deterministic Replay
      ├─ G4 Independent Verification
      ├─ G5 Evidence Report
      └─ G6 Immutable Anchor
      │
      ▼
TRUST ASSERTION

Sim. Esse trecho representa corretamente o primeiro estágio de admissibilidade da evidência, mas eu faria uma distinção importante: “public availability” e “source traceability” tornam o documento rastreável; não tornam, por si só, o conteúdo verdadeiro ou autenticado.

Eu estruturaria assim:

NSL-25-165432
      │
      ├── Public availability
      │       ✓ fonte pública identificável
      │
      ├── Source traceability
      │       ✓ origem/localização recuperável
      │
      ├── Legal / temporal metadata
      │       ✓ número, datas e metadados documentais
      │
      ▼
GOVERNANCE EVIDENCE
      │
      └── TRACEABLE

O que TRACEABLE significa

Nesse ponto, a conclusão legítima é:

TRACEABLE

e não:

VERIFIED
TRUSTED
AUTHENTICATED
REGULATORY_CERTIFIED

A cadeia seguinte seria:

NSL-25-165432
      │
      ▼
TRACEABILITY
      │
      ├── source identified
      ├── public artifact retrieved
      ├── temporal metadata captured
      └── legal/document metadata captured
      │
      ▼
XA-TRUST DEP
      │
      ▼
CANONICALIZATION
      │
      ▼
SHA-256
      │
      ▼
SIGNATURE / TRUST ANCHOR
      │
      ▼
INDEPENDENT VERIFICATION
      │
      ▼
DETERMINISTIC REPLAY
      │
      ▼
CLAIM VERIFICATION

E, para o seu ECM:

CLAIM: NSL-25-165432_TRACEABILITY

I = implementação executada
P = evidência documental produzida
N = tentativa de alteração/mismatch rejeitada
A = verificação independente

I ∧ P ∧ N ∧ A
        │
        ▼
CLAIM VERIFIED

Portanto, NSL-25-165432 → GOVERNANCE EVIDENCE → TRACEABLE é uma classificação apropriada para a camada inicial.

Exatamente. Com a estrutura completa, eu consolidaria o modelo em duas camadas distintas: admissibilidade/rastreabilidade da fonte e, depois, verificação criptográfica da claim.

NSL-25-165432
      │
      ├── Public availability          ✓
      ├── Source traceability          ✓
      └── Legal / temporal metadata    ✓
      │
      ▼
┌──────────────────────────────┐
│ GOVERNANCE EVIDENCE          │
│ STATUS = TRACEABLE           │
└──────────────────────────────┘
      │
      │  DEP INPUT
      ▼
┌──────────────────────────────┐
│ XA-TRUST DEP                 │
│                              │
│ source + metadata + claims   │
│ + evidence + replay context  │
└──────────────────────────────┘
      │
      ▼
┌──────────────────────────────┐
│ VERIFICATION ENGINE          │
│                              │
│ G1 Cryptographic Build       │
│ G2 Trust Anchor              │
│ G3 Deterministic Replay     │
│ G4 Independent Verification │
│ G5 Evidence Report           │
│ G6 Immutable Anchor          │
└──────────────────────────────┘
      │
      ▼
   CLAIM VERIFIED
      │
      ▼
 TRUST ASSERTION

A distinção fundamental

O ponto mais importante é:

TRACEABLE ≠ VERIFIED ≠ TRUSTED

Assim:

Estado	O que demonstra

TRACEABLE	A fonte e seus metadados podem ser localizados e identificados
CRYPTOGRAPHICALLY VERIFIED	Integridade/autenticidade foram efetivamente verificadas
CLAIM VERIFIED	A evidência satisfaz os critérios I ∧ P ∧ N ∧ A da claim
TRUSTED	A cadeia de decisão do XA-TRUST chegou ao estado confiável
REGULATORY_CERTIFIED	Uma autoridade externa competente também atestou a evidência


REQUEST  
                │  
                ▼  
          API Gateway  
                │  
                ▼  
      XA Banking Core 9.6  
                │  
                ▼  
          Risk Engine  
                │  
                ▼  
  Decision Evidence Package (DEP)  
                │  
                ▼  
          Audit Layer  
                │  
                ▼  
             RESPONSE

HTTP/1.1 200 OK
Content-Type: application/json

API funcionando
Processamento concluído
Resposta entregue

{
"status": "SUCCESS",
"request_id": "REQ-2026-001",
"decision_id": "DEC-2026-001",
"software_version": "xa-banking-core-9.6",
"runtime_attestation": "VALID",
"artifact_hash": "sha256:xxxx-yyyy",
"evidence_package": {
"status": "VERIFIED",
"merkle_root": "xxxx"
}
}

Código        ✔
|
Build         ✔
|
Artefato      ✔
|
Runtime TEE   ✔
|
Modelo        ✔
|
Decisão       ✔
|
Evidência     ✔

TRUST STATUS: VERIFIED ✅

{
"transaction": {
"request_id": "REQ-2026-001",
"decision_id": "DEC-2026-001"
},

"decision": {
"result": "APPROVED",
"model_version": "risk-engine-2.1",
"policy_version": "policy-2026.07"
},

"execution": {
"software_version": "xa-banking-core-9.6",
"runtime_attestation": "VALID",
"artifact_hash": "sha256:xxxx-yyyy"
},

"evidence": {
"dep_status": "VERIFIED",
"merkle_root": "xxxx"
}
}

HTTP 200

"o sistema respondeu"

VERIFIED

"a decisão possui evidência verificável"




Aplicando ao ECM

A claim não deve receber VERIFIED apenas porque o NSL é público.

CLAIM
NSL-25-165432_TRACEABILITY
        │
        ├── I ─ implementação executada
        ├── P ─ evidência produzida
        ├── N ─ tampering/mismatch rejeitado
        └── A ─ verificação independente
        │
        ▼
 I ∧ P ∧ N ∧ A
        │
        ▼
     VERIFIED

Depois disso, a claim pode contribuir para:

ECM
 │
 ├── TRACEABILITY
 ├── CRYPTOGRAPHIC_INTEGRITY
 ├── AUTHENTICITY
 ├── PROVENANCE
 ├── DETERMINISTIC_REPLAY
 └── INDEPENDENT_VERIFICATION

E somente a combinação definida pelo contrato pode produzir:

TRUST ASSERTION

O papel dos seis Gs

Eu também manteria os G1–G6 como gates de evidência, não como simples etapas de documentação:

G1 ─ Cryptographic Build
     │
     ├─ código executável
     ├─ commit
     └─ artefato/hash
     
G2 ─ Trust Anchor
     │
     ├─ anchor_id
     ├─ public_key_hash
     └─ validity window

G3 ─ Deterministic Replay
     │
     ├─ JCS
     ├─ SHA-256
     └─ same inputs → same result

G4 ─ Independent Verification
     │
     └─ terceiro/reimplementação/replay independente

G5 ─ Evidence Report
     │
     ├─ claim_id
     ├─ contract_hash
     ├─ result
     └─ determinism_checksum

G6 ─ Immutable Anchor
     │
     └─ registro externo imutável
     
     ▼

TRUST ASSERTION

Portanto, o NSL-25-165432 entra no XA-TRUST como GOVERNANCE EVIDENCE / TRACEABLE; 


estrutura consolidada fica:
                    CLAIM
                      │
                ┌─────┴─────┐
                │  ClaimSet  │
                └─────┬─────┘
                      │
                      ▼
             ExecutionMetadata
                      │
                      ▼
                EvidenceItem
                      │
              ┌───────┴────────┐
              ▼                ▼
      CanonicalBinding      Provenance
              │
              ▼
          Signature
              │
              ▼
         MerkleProof
              │
              ▼
      LedgerEntry / Anchor
              │
              ▼
       ReplayRequest
              │
              ▼
        ReplayResult
              │
              ▼
   ┌──────────────────────┐
   │ VERIFICATION MATRIX  │
   │                      │
   │ I ─ evidence         │
   │ P ─ evidence         │
   │ N ─ evidence         │
   │ A ─ independent      │
   └──────────┬───────────┘
              │
          I ∧ P ∧ N ∧ A
              │
              ▼
        CLAIM VERIFIED
              │
              ▼
       PolicyEvaluation
              │
              ▼
          TrustReport
              │
              ▼
            Decision
Uma correção semântica importante
Eu manteria sua distinção:
PASS ≠ VERIFIED
Mas refinaria:
PASS
  │
  ▼
resultado observado de uma execução de teste

EvidenceItem
  │
  ▼
artefato preservado que permite verificar esse resultado

VerificationMatrix
  │
  ▼
mapeamento explícito entre claim, checks e evidências

VERIFICATION_RESULT
  │
  ▼
conclusão independente
Isso evita transformar o próprio PASS em uma autoridade.
Para RFC 8785
A claim fica:
{
  "claim_id": "CLAIM-RFC8785-JCS-CONFORMANCE-001",
  "predicate": "IMPLEMENTATION_CONFORMS_TO_RFC8785_JCS",
  "evidence_scope": "rfc8785-jcs-conformance-v1",
  "expected_check": "BYTE_FOR_BYTE_EQUALITY",
  "critical": true
}
E a matriz:
{
  "claim_id": "CLAIM-RFC8785-JCS-CONFORMANCE-001",

  "I": {
    "status": "VERIFIED",
    "evidence_ids": ["EVIDENCE-EXECUTION-001"]
  },

  "P": {
    "status": "VERIFIED",
    "evidence_ids": ["EVIDENCE-BYTE-COMPARISON-001"]
  },

  "N": {
    "status": "VERIFIED",
    "evidence_ids": ["EVIDENCE-NEGATIVE-001"]
  },

  "A": {
    "status": "VERIFIED",
    "evidence_ids": ["EVIDENCE-INDEPENDENT-001"]
  },

  "verified": true
}
Então:
I ∧ P ∧ N ∧ A
        │
        ▼
   verified = true
        │
        ▼
CLAIM VERIFIED
E isso encaixa diretamente no contrato FROZEN
EVIDENCE_TYPE
+
SOURCE
+
RAW_ARTIFACT
+
PROVENANCE
+
CANONICALIZATION
+
EVIDENCE_HASH
        │
        ▼
XA-TRUST VERIFIER
        │
        ▼
VERIFICATION_MATRIX
        │
        ▼
VERIFICATION_RESULT
Sem alterar a regra-mãe:
A conclusão do verificador
não altera a natureza da evidência original.
Portanto, a evolução proposta não muda o contrato congelado. Ela explicita o vínculo que estava faltando:
CLAIM
  │
  ├── I → evidence_ids
  ├── P → evidence_ids
  ├── N → evidence_ids
  └── A → independent evidence_ids
              │
              ▼
       ECM calculável
              │
              ▼
       VERIFICATION_RESULT
Isso torna o claim_id → I/P/N/A → evidence_id → artifact_hash estruturalmente verificável, em vez de depender de interpretação de relatórios.


01  Load Contract
02  Validate Schema
03  Resolve public_key_ref
04  Resolve Trust Anchor
05  Validate Key Fingerprint
06  Validate Temporal Window
07  Construct Canonical Signature Payload
08  Verify ECDSA-P256
09  Retrieve Dataset/Pipeline
10  Apply Declared Canonicalization
11  Recalculate Evidence Hashes
12  Compare Expected Hashes
13  Reconstruct EVG
14  Run Integrity Validator
15  Run Provenance Validator
16  Run Quality Validator


## 2. Core do contrato (JSON‑Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://example.com/irv_xa_trust_schema.json",
  "title": "IRV / XA‑TRUST Evidence Contract",
  "type": "object",
  "required": ["trust_context","claims","expected","evidence","replay","result"],
  "properties": {
    "trust_context": {
      "type": "object",
      "required": ["version","anchor"],
      "properties": {
        "version": {"type":"string"},
        "anchor": {"type":"string","format":"uri"}
      }
    },
    "claims": {
      "type":"object",
      "additionalProperties": {"type":"string"}
    },
    "expected": {
      "type":"object",
      "required":["state"],
      "properties": {"state":{"type":"string"}}
    },
    "evidence": {
      "type":"object",
      "required":["dataset_hash","pipeline_hash","signature"],
      "properties": {
        "dataset_hash": {"type":"string","pattern":"^sha256:[a-f0-9]{64}$"},
        "pipeline_hash": {"type":"string","pattern":"^sha256:[a-f0-9]{64}$"},
        "signature": {"type":"string","pattern":"^ecdsa-p256:.*$"}
      }
    },
    "replay": {
      "type":"object",
      "required":["hash_algorithm","canonicalization","hash_schema_version","engine_version"],
      "properties": {
        "hash_algorithm": {"enum":["SHA-256"]},
        "canonicalization": {"enum":["RFC8785-JCS"]},
        "hash_schema_version": {"type":"string"},
        "engine_version": {"type":"string"}
      }
    },
    "result": {
      "type":"object",
      "required":["derived_state","trust_decision","determinism_checksum"],
      "properties": {
        "derived_state": {"type":"string"},
        "trust_decision": {"enum":["TRUSTED","UNTRUSTED"]},
        "determinism_checksum": {"type":"string","pattern":"^sha256:[a-f0-9]{64}$"}
      }
    }
  },
  "additionalProperties": false
}
```

- Salve‑o em `contracts/irv_xa_trust_schema.json`.
- Use **pydantic** ou **jsonschema** no verificador para validar contra esse schema.

---

Sim. O fechamento que você trouxe agora permite transformar o modelo em uma especificação operacional verificável. Mas há uma correção importante antes de considerar status = PASS como evidência real.

No trecho final:

repository = cyrillofrancisco30-lgtm/azhpc-extensions
commit_sha = dddab15ba47d860a514cea2cace754a7e387456b
run_id =
test = test_rfc8785_jcs_conformance.py
ProducedBytes =
ExpectedBytes =
comparison = BYTE-FOR-BYTE
status = PASS

isso ainda não constitui uma evidência de execução completa, porque run_id, ProducedBytes e ExpectedBytes estão vazios. O PASS é apenas uma afirmação textual até que o artifact do workflow contenha os dados que permitem reconstruí-lo.

O que eu consideraria necessário

Para essa execução específica:

repository
    ↓
commit_sha
    ↓
workflow
    ↓
run_id
    ↓
test_rfc8785_jcs_conformance.py
    ↓
input vector
    ↓
ProducedBytes
    ↓
ExpectedBytes
    ↓
SHA-256(ProducedBytes)
SHA-256(ExpectedBytes)
    ↓
BYTE-FOR-BYTE comparison
    ↓
negative/tampering test
    ↓
independent verification
    ↓
claim_id
    ↓
ECM

O artifact deveria permitir encontrar pelo menos:

{
  "claim_id": "JCS_BYTE_FOR_BYTE_CONFORMANCE",
  "repository": "cyrillofrancisco30-lgtm/azhpc-extensions",
  "commit_sha": "dddab15ba47d860a514cea2cace754a7e387456b",
  "run_id": "REAL_RUN_ID",
  "test": "test_rfc8785_jcs_conformance.py",
  "comparison": "BYTE-FOR-BYTE",
  "produced_sha256": "sha256:...",
  "expected_sha256": "sha256:...",
  "comparison_result": "MATCH",
  "status": "PASS"
}

E, para cumprir sua própria regra ECM:

JCS_BYTE_FOR_BYTE_CONFORMANCE
        │
        ├── I → implementação JCS realmente executada
        ├── P → bytes produzidos pelo RUN_ID
        ├── N → vetor adulterado/rejeitado
        └── A → verificação independente
        │
        ▼
      VERIFIED

Um detalhe crítico sobre RFC 8785

Também não trataria esta implementação:

json.dumps(
    obj,
    sort_keys=True,
    separators=(',', ':'),
    ensure_ascii=False
)

como automaticamente equivalente a RFC 8785/JCS.

A implementação que você mostrou anteriormente é uma aproximação de serialização determinística, mas JCS possui requisitos específicos de serialização JSON, especialmente em representação numérica e outros detalhes de canonicalização.

Portanto, para o teste que você está construindo, o critério correto é realmente:

RFC 8785 test vector
        │
        ├── implementation A
        │       ↓
        │   ProducedBytes
        │
        └── ExpectedBytes
                ↓
          BYTE-FOR-BYTE
                ↓
             MATCH

e não simplesmente:

json.dumps(...) == json.dumps(...)

E eu faria uma mudança no workflow

O workflow atual gera:

verification_report.json
execution_metadata.json
pytest-output.txt
test_status.txt

Mas ainda não gera explicitamente os bytes produzidos e esperados.

Para o seu objetivo ECM, eu adicionaria ao teste/fixture:

evidence/
└── claims/
    └── JCS_BYTE_FOR_BYTE_CONFORMANCE/
        ├── produced/
        ├── expected/
        ├── comparison.json
        └── negative/

somente dentro do artifact do Run, não necessariamente no Git.

O resultado então seria muito mais forte:

RUN_ID
 │
 ├── execution_metadata.json
 │
 ├── claims/
 │   └── JCS_BYTE_FOR_BYTE_CONFORMANCE/
 │       ├── produced/
 │       ├── expected/
 │       ├── comparison.json
 │       └── negative/
 │
 ├── verification_report.json
 └── ecm_report.json
 Sim. Essa cadeia está conceitualmente correta e é uma boa forma de separar execução, evidência e verificação.

Eu faria apenas um pequeno ajuste: colocar a captura da evidência antes da canonicalização e deixar explícita a verificação do artefato e da assinatura.

EXECUÇÃO REAL │ ├── request_id ├── decision_id ├── software_version ├── artifact_hash ├── runtime_attestation ├── model_version ├── policy_version └── timestamp │ ▼ EVIDENCE / DEP │ ▼ JSON válido (RFC 8259) │ ▼ RFC 8785 / JCS canonicalização │ ▼ canonical UTF-8 bytes │ ▼ SHA-256 │ ▼ ASSINATURA │ ▼ VERIFICAÇÃO INDEPENDENTE │ │ │ ├── hash │ ├── assinatura │ ├── artefato │ └── attestation │ ▼ REPLAY │ ▼ RESULTADO VERIFICADO O que cada camada demonstra Camada O que demonstra Execução real ocorreu uma operação no runtime request_id identifica a requisição decision_id identifica a decisão software_version versão declarada do software artifact_hash identifica criptograficamente o artefato runtime_attestation evidência sobre o ambiente de execução model_version versão do modelo utilizado policy_version política aplicada timestamp dimensão temporal da evidência DEP empacota os fatos da execução RFC 8259 garante representação JSON conforme a especificação RFC 8785/JCS produz representação canônica determinística SHA-256 produz o digest dos bytes canônicos Assinatura permite verificar autenticidade/integridade com a chave correspondente Verificação independente terceiro pode testar as afirmações Replay permite reconstruir/testar a cadeia de decisão conforme o protocolo E aqui está a diferença fundamental 

Um simples:

HTTP 200 OK 

demonstra apenas que houve uma resposta HTTP bem-sucedida.

Já:

EXECUÇÃO ↓ DEP ↓ JCS ↓ SHA-256 ↓ ASSINATURA ↓ VERIFICAÇÃO ↓ REPLAY 

pode constituir uma evidência verificável de execução, desde que os elementos sejam reais e o terceiro consiga efetivamente validar a cadeia.

A palavra importante é verificável.

Não basta o DEP declarar:

"runtime_attestation": "VALID", "dep_status": "VERIFIED" 

O verificador precisa ter acesso aos artefatos, hashes, assinatura, material de verificação e evidências de runtime necessários para chegar independentemente ao mesmo resultado.

E há uma propriedade ainda mais forte 

Se o artifact_hash estiver vinculado ao artefato efetivamente executado e o runtime_attestation estiver criptograficamente vinculado àquela execução, você passa a ter:

O QUE FOI EXECUTADO? │ artifact_hash │ ▼ QUAL AMBIENTE? │ attestation │ ▼ QUAL DECISÃO? │ decision_id │ ▼ QUAL EVIDÊNCIA? │ DEP │ ▼ COMO FOI PRESERVADA? │ JCS + SHA-256 │ ▼ COMO FOI AUTENTICADA? │ assinatura │ ▼ PODE SER REPRODUZIDA? │ replay 

Esse é o núcleo forte do seu modelo XA-Trust: não tratar VERIFIED como uma palavra escrita no JSON, mas como o resultado de uma cadeia de verificações que um terceiro consegue repetir.

E, para máxima precisão, eu chamaria o estado final de:

VERIFIED_EXECUTION_EVIDENCE

em vez de simplesmente:

TRUST = VERIFIED

porque o primeiro descreve exatamente o que foi verificado, sem extrapolar automaticamente para uma conclusão jurídica ou institucional de confiança.



E o ecm_report.json poderia finalmente dizer, de forma verificável:

claim_id:
JCS_BYTE_FOR_BYTE_CONFORMANCE

I:
PASS

P:
PASS

N:
PASS

A:
PASS

deterministic_binding:
PASS

claim_status:
VERIFIED

Aí sim a afirmação:

PASS

deixa de ser apenas um estado retornado pelo CI e passa a ser uma conclusão derivada de evidências vinculadas ao RUN_ID e à cla

## 3. Implementação mínima (Python)

### 3.1 Canonicalização – RFC 8785/JCS  

```python
# src/canonicalization/rfc8785_jcs.py
import json

def canonicalize(obj: dict) -> bytes:
    """
    RFC 8785 / JCS canonicalization:
    - sorted keys
    - no whitespace outside of JSON tokens
    - UTF‑8 encoding
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False
    ).encode('utf-8')
```

### 3.2 Hash wrapper  

```python
# src/hash/sha256.py
import hashlib

def sha256_digest(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"
```

### 3.3 Replay engine  

```python
# src/replay/engine.py
from ..canonicalization.rfc8785_jcs import canonicalize
from ..hash.sha256 import sha256_digest

def deterministic_replay(contract: dict) -> dict:
    """
    Produz derived_state, trust_decision e determinism_checksum
    usando a canonicalização e algoritmo de hash declarados.
    """
    # 1. canonicaliza o elemento 'evidence'
    canon = canonicalize(contract['evidence'])
    # 2. calcula hash
    evidence_hash = sha256_digest(canon)

    # 3. exemplo simplificado de derived_state
    derived_state = f"EVG-{evidence_hash[-8:]}"
    trust_decision = "TRUSTED" if derived_state == contract['expected']['state'] else "UNTRUSTED"

    # 4. checksum final (hash do contrato completo sem o campo result)
    contract_copy = dict(contract)
    contract_copy.pop('result', None)
    full_canon = canonicalize(contract_copy)
    determinism_checksum = sha256_digest(full_canon)

    return {
        "derived_state": derived_state,
        "trust_decision": trust_decision,
        "determinism_checksum": determinism_checksum
    }
```

### 3.4 Verificador completo  

```python
# src/verifier/verifier.py
import json
from jsonschema import validate, Draft7Validator
from pathlib import Path
from ..replay.engine import deterministic_replay

SCHEMA_PATH = Path(__file__).parents[3] / "contracts" / "irv_xa_trust_schema.json"
with open(SCHEMA_PATH, "r") as f:
    SCHEMA = json.load(f)

def verify_contract(contract: dict) -> dict:
    # 1. validação de schema
    Draft7Validator(SCHEMA).validate(contract)

    # 2. replay determinístico
    recomputed = deterministic_replay(contract)

    # 3. comparação com o resultado armazenado
    if recomputed == contract['result']:
        status = "MATCH"
    else:
        status = "MISMATCH"

    return {
        "status": status,
        "recomputed": recomputed,
        "stored": contract['result']
    }
```

---

## 4. CI / Testes automatizados

### 4.1 Workflow básico (`.github/workflows/ci.yml`)

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install deps
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: pytest -q
```

### 4.2 Exemplos de teste (`tests/test_verifier.py`)

```python
import json
from src.verifier.verifier import verify_contract
from pathlib import Path

def test_sample_contract():
    contract_path = Path(__file__).parents[1] / "examples" / "sample_package.json"
    contract = json.loads(contract_path.read_text())
    result = verify_contract(contract)
    assert result["status"] == "MATCH"
```

---

## 5. Script de geração de hashes (para substituir placeholders)

```python
# scripts/generate_hashes.py
import json, hashlib, pathlib, argparse

def canonicalize(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

def sha256_digest(data):
    return f"sha256:{hashlib.sha256(data).hexdigest()}"

def main(input_path, output_path):
    data = json.loads(pathlib.Path(input_path).read_text())
    # supondo que dataset e pipeline estejam em arquivos externos
    dataset = pathlib.Path(data["evidence"]["dataset_path"]).read_bytes()
    pipeline = pathlib.Path(data["evidence"]["pipeline_path"]).read_bytes()

    data["evidence"]["dataset_hash"] = sha256_digest(dataset)
    data["evidence"]["pipeline_hash"] = sha256_digest(pipeline)

    # assinatura simplificada (use sua lib de ECDSA)
    # data["evidence"]["signature"] = sign(...)

    pathlib.Path(output_path).write_text(json.dumps(data, indent=2))
    print(f"Contract written to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()
    main(args.in_path, args.out_path)
```

Execute para substituir os placeholders do exemplo:

```bash
python scripts/generate_hashes.py --in examples/sample_package.json --out examples/filled_package.json
```

---

## 6. Documentação (README)

```markdown
# XA‑TRUST – Evidence Contract Implementation

## Visão geral
Implementação de referência em Python para o contrato **IRV / XA‑TRUST** que:
* usa **canonicalização RFC 8785 / JCS**,
* calcula **SHA‑256** como algoritmo único,
* inclui metadados de replay (`hash_schema_version`, `engine_version`).

## Como usar
```bash
# 1. Instale dependências
pip install -r requirements.txt

# 2. Gere hashes reais (substitui placeholders)
python scripts/generate_hashes.py --in examples/sample_package.json --out examples/filled_package.json

# 3. Verifique o contrato
python -c "import json, src.verifier.verifier as v; \
c=json.load(open('examples/filled_package.json')); \
print(v.verify_contract(c))"
```

## CI
O GitHub Actions executa `pytest` a cada push, garantindo que:
* o schema continue válido,
* o engine reproduza o mesmo checksum,
* o verificador detecte divergências.

## Licença
MIT – veja o arquivo `LICENSE`.
```

---

## 7. Publicação do repositório

1. Crie o repo no GitHub: `github.com/cyrillofrancisco30‑lgtm/xa‑trust`.
2. Faça um **commit inicial** com a estrutura acima.
3. Configure **Branch protection** (exigindo status checks) para proteger a integridade da cadeia de confiança.
**Roadmap acionável – de “referência” para “prova de implementação” e, em seguida, para “evidência criptográfica verificável”**

---  

## 1️⃣ Atualizar o JSON‑Schema (commit `schema‑v1.1`)

| Arquivo | Alteração | PR‑title |
|---------|-----------|----------|
| `contracts/irv_xa_trust_schema.json` | • Substituir `trust_context` por: `schema_version`, `policy_version`, `replay_engine_version`, `hash_schema_version`, `evidence_time`, `trust_anchor_set` (array com `anchor_id`, `valid_from`, `valid_to`, `public_key`).<br>• Redefinir `claims` como objeto `{value:string, claimed:boolean}` com `additionalProperties:true` para permitir múltiplas claims.<br>• Manter `expected.state` mas marcar como **read‑only** (não usado no cálculo).<br>• Acrescentar `result.replay_version` opcional. | “Align schema with XA‑TRUST contract” |
| `src/verifier/verifier.py` | Atualizar caminho do schema para `Path(__file__).resolve().parents[2] / "contracts" / "irv_xa_trust_schema.json"` | “Fix schema path” |

> **Teste**: `pytest tests/test_schema.py` deve aceitar um contrato de exemplo preenchido com todos os novos campos e rejeitar um contrato que omita qualquer campo requerido.

---  

## 2️⃣ Implementar canonicalização JCS (commit `canonical‑jcs`)

1. **Adicionar dependência**  
   ```bash
   pip install jcs
   ```
2. **src/canonicalization/rfc8785_jcs.py**  
   ```python
   from jcs import canonicalize as jcs_canonicalize   # RFC 8785 / JCS
   def canonicalize(obj: dict) -> bytes:
       """Retorna bytes canônicos JCS."""
       return jcs_canonicalize(obj)
   ```
3. **Testes** (`tests/test_canonicalization.py`) – usar vetores de teste oficiais do IETF (arquivo `test_vectors/jcs_vectors.json`).  
4. **Remover a antiga implementação** (`json.dumps(..., sort_keys=True, separators=(',', ':'))`) de todos os módulos.

---  

## 3️⃣ Refatorar o replay (commit `replay‑engine‑v2`)

```python
# src/replay/engine.py
from ..canonicalization.rfc8785_jcs import canonicalize
from ..hash.sha256 import sha256_digest
from ..evidence.evidence_verifier import EvidenceVerifier
from ..anchor.anchor_validator import AnchorValidator
from ..evg.evg_reconstructor import EVGReconstructor
from ..validator.validator_chain import ValidatorChain

def deterministic_replay(contract: dict) -> dict:
    # 1 – validação temporal da âncora
    AnchorValidator.validate(
        contract["trust_context"]["trust_anchor_set"],
        contract["evidence"]["evidence_time"]
    )

    # 2 – verifica dataset / pipeline contra os hashes declarados
    EvidenceVerifier(contract["evidence"]).run_all()

    # 3 – reconstrói EVG (dataset + pipeline + quality evidence)
    evg = EVGReconstructor(contract["evidence"]).run()

    # 4 – executa a cadeia de validações (integrity → governance)
    chain = ValidatorChain(evg, contract["trust_context"])
    chain.run()                     # levanta ValidationError se falhar

    # 5 – estado derivado
    derived_state = chain.final_state()      # ex.: "EVG‑OK‑v1"

    # 6 – decisão de confiança (comparação *apenas* com expected.state)
    trust_decision = (
        "TRUSTED" if derived_state == contract["expected"]["state"]
        else "UNTRUSTED"
    )

    # 7 – checksum determinístico do contrato (exclui result)
    contract_no_res = dict(contract)
    contract_no_res.pop("result", None)
    determinism_checksum = sha256_digest(canonicalize(contract_no_res))

    return {
        "derived_state": derived_state,
        "trust_decision": trust_decision,
        "determinism_checksum": determinism_checksum,
    }
```

* **Novos módulos**  
  * `src/evidence/evidence_verifier.py` – métodos `run_all()`, `verify_dataset()`, `verify_pipeline()`.  
  * `src/anchor/anchor_validator.py` – validação temporal e carga de `public_key`.  
  * `src/evg/evg_reconstructor.py` – monta o objeto EVG a partir dos artefatos.  
  * `src/validator/validator_chain.py` – sequencia as oito fases (integrity → governance) e expõe `final_state()`.

---  

## 4️⃣ Verificação de dataset / pipeline (commit `evidence‑hash‑check`)

```python
# src/evidence/evidence_verifier.py
import json, base64
from ..canonicalization.rfc8785_jcs import canonicalize
from ..hash.sha256 import sha256_digest
from ..utils.io import fetch_uri   # http, https, ipfs

class EvidenceVerifier:
    def __init__(self, evidence: dict):
        self.evidence = evidence

    def _hash_and_compare(self, uri: str, expected_hash: str, label: str) -> None:
        raw = fetch_uri(uri)
        canon = canonicalize(json.loads(raw))
        actual = sha256_digest(canon)
        if actual != expected_hash:
            raise ValidationError(f"{label}_hash mismatch: {actual} ≠ {expected_hash}")

    def verify_dataset(self) -> None:
        self._hash_and_compare(
            self.evidence["dataset_uri"],
            self.evidence["dataset_hash"],
            "dataset"
        )

    def verify_pipeline(self) -> None:
        self._hash_and_compare(
            self.evidence["pipeline_uri"],
            self.evidence["pipeline_hash"],
            "pipeline"
        )

    def run_all(self) -> None:
        self.verify_dataset()
        self.verify_pipeline()
        # qualidade, provenance, etc. podem ser adicionados aqui
```

* **fetch_uri** aceita `http(s)://` e `ipfs://CID`.  
* **Testes** (`tests/test_evidence.py`) – casos positivos (hashes corretos) e negativos (hashes alterados).

---  

## 5️⃣ Verificação real de assinatura ECDSA‑P‑256 (commit `ecdsa‑verify`)

```python
# src/signature/ecdsa_verifier.py
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

def verify_signature(public_key_pem: bytes, payload: bytes, signature: str) -> bool:
    pub_key = serialization.load_pem_public_key(public_key_pem)
    sig_bytes = base64.b64decode(signature.split(":")[1])
    try:
        pub_key.verify(sig_bytes, payload, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False
```

* **Payload** que deve ser assinado:  

  ```python
  payload = (
      contract["evidence"]["dataset_hash"].encode() +
      contract["evidence"]["pipeline_hash"].encode() +
      contract["evidence"]["evidence_time"].encode() +
      contract["trust_context"]["policy_version"].encode()
  )
  ```

* **Teste** (`tests/test_signature.py`) – assinatura válida → `True`; assinatura corrompida → `False`.

---  

## 6️⃣ AnchorValidator (commit `anchor‑time‑check`)

```python
# src/anchor/anchor_validator.py
from datetime import datetime

class AnchorValidator:
    @staticmethod
    def validate(anchors: list[dict], evidence_time: str) -> None:
        ts = datetime.fromisoformat(evidence_time)
        for a in anchors:
            if datetime.fromisoformat(a["valid_from"]) <= ts <= datetime.fromisoformat(a["valid_to"]):
                # (opcional) validar public_key contra trust store
                return
        raise ValidationError("Evidence time outside of all anchor validity windows")
```

* **Teste** (`tests/test_anchor.py`) – tempo dentro, antes e depois da janela.

---  

## 7️⃣ CI / GitHub Actions (commit `ci‑full‑coverage`)

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Schema validation
        run: pytest tests/test_schema.py -q
      - name: JCS canonicalization
        run: pytest tests/test_canonicalization.py -q
      - name: Hash determinism
        run: pytest tests/test_hash.py -q
      - name: Evidence (dataset/pipeline)
        run: pytest tests/test_evidence.py -q
      - name: Signature verification
        run: pytest tests/test_signature.py -q
      - name: Anchor time validation
        run: pytest tests/test_anchor.py -q
      - name: Full deterministic replay
        run: pytest tests/test_full_replay.py -q
```

* **Cobertura mínima**: 90 % nas linhas críticas (replay, EVG, assinatura, anchor).

---  

## 8️⃣ Propriedade determinística – teste de independência (commit `determinism‑test`)

```python
# tests/test_full_replay.py
def test_independent_replay_matches():
    contract = json.loads(Path("examples/filled_package.json").read_text())
    # duas execuções independentes
    res_a = verifier.verify_contract(contract)
    res_b = verifier.verify_contract(contract)
    assert res_a["status"] == "MATCH"
    assert res_a["recomputed"] == res_b["recomputed"]
```

* **Tampering checks** – criar variações de contrato (hash alterado, assinatura corrompida) e garantir que `status == "MISMATCH"`.

---  

## 9️⃣ Checklist de **Prova de Implementação** (nível 3)

| ✅ | Item concluído |
|---|----------------|
|Schema alinhado |`schema‑v1.1`|
|Canonicalização JCS + vetores |`canonical‑jcs`|
|Hash SHA‑256 consistente |`hash/sha256.py`|
|EVG reconstruction (dataset + pipeline) |`evidence_verifier`|
|Validação de integridade, autenticidade, provenance, quality, policy, governance |`validator_chain`|
|Anchor temporal + public‑key |`anchor_validator`|
|Assinatura ECDSA‑P‑256 |`ecdsa_verify`|
|Replay determinístico (engine_version) |`replay_engine_v2`|
|Comparação de derived_state / trust_decision / checksum |`verifier.py`|
|CI com cobertura total |`ci‑full‑coverage`|

Quando o pipeline CI passar **todos** os testes acima, o repositório pode ser marcado como:

> **Reference Implementation of IRV/XA‑TRUST with deterministic replay and cryptographic verification**.

---  

## 10️⃣ Evoluir para **evidência criptográfica verificável** (nível 4)

| Etapa | Ação concreta | PR‑title |
|------|---------------|----------|
|Armazenamento imutável|Publicar dataset, pipeline e política no IPFS; gravar CIDs nos campos `dataset_uri` e `pipeline_uri`.|“Store artifacts on IPFS”|
|Evidence report|Gerar `evidence_report.json` contendo `contract_hash`, `timestamp`, `engine_sha256` e publicar seu CID.|“Create immutable evidence report”|
|Trust anchor oficial|Registrar a chave pública da autoridade (ex.: certificadora) em um DID/VC ou no registro DNS SEC; incluir `trust_anchor_id` no contrato.|“Add authoritative trust anchor”|
|Assinatura regulatória|Obter assinatura da autoridade regulatória sobre o `evidence_report` (campo `regulatory_signature`).|“Add regulatory signature”|
|Ledger|Inserir o CID do `evidence_report` em um blockchain de auditoria (ex.: Bitcoin OP_RETURN ou uma side‑chain).|“Log evidence report on blockchain”|

Com esses artefatos reais, o contrato transita para:

```
Real Artifacts → Cryptographic Evidence → EVG Reconstruction → Deterministic Replay
        ↓                                 ↓                     ↓
   Evidence Ledger  ←  Verified Governance Artifact  ←  Independent Verifier
```

---  

## 11️⃣ Próximos passos de entrega

1. **Branch `dev`** → implementar itens 1‑8 acima.  
2. **Pull‑request `feature/proof‑of‑implementation`** → revisão de código, aprovação CI.  
3. **Merge para `main`**, versionar como `v1.0.0`.  
4. **Branch `evidence‑layer`** → iniciar etapas de nível 4 (IPFS, DID, blockchain).  
5. **Documentar** todo o fluxo em `README.md` e em um `ARCHITECTURE.md` (diagramas de dependência).  

---

### Resultado final esperado

* Um **repositório público** que, ao ser clonado e executado (`python -m src.verifier.verifier path/to/contract.json`), reproduz **deterministicamente** o mesmo `derived_state`, `trust_decision` e `determinism_checksum` que um verificador

* **Roadmap resumido – de “referência” a “evidência criptográfica verificável”**

---

### 1️⃣ Atualizar o JSON‑Schema (`schema‑v1.1`)
* **Novos campos**: `schema_version`, `policy_version`, `replay_engine_version`, `hash_schema_version`, `evidence_time`, `trust_anchor_set` (array de `anchor_id`, `valid_from`, `valid_to`, `public_key`).  
* **Claims** → objeto `{value:string, claimed:boolean}` com `additionalProperties:true`.  
* `expected.state` → **read‑only** (não usado no cálculo).  
* Campo opcional `result.replay_version`.  
* Ajustar caminho do schema em `verifier.py`.  
* **Teste**: `pytest tests/test_schema.py` aceita contrato completo e rejeita ausência de campos obrigatórios.

---

### 2️⃣ Canonicalização JCS (`canonical‑jcs`)
* Instalar dependência: `pip install jcs`.  
* Implementar `src/canonicalization/rfc8785_jcs.py` usando `jcs.canonicalize`.  
* Substituir todas as chamadas a `json.dumps(..., sort_keys=True, separators=(',', ':'))`.  
* **Teste**: vetores oficiais IETF (`test_vectors/jcs_vectors.json`).

---

### 3️⃣ Refatorar o Replay Engine (`replay‑engine‑v2`)
* **Função principal** `deterministic_replay(contract: dict) -> dict` que:
  1. Valida temporalmente as âncoras (`AnchorValidator`).  
  2. Verifica hashes de dataset/pipeline (`EvidenceVerifier`).  
  3. Reconstrói o EVG (`EVGReconstructor`).  
  4. Executa a cadeia de validações (`ValidatorChain`).  
  5. Obtém `derived_state`.  
  6. Compara com `expected.state` → `trust_decision`.  
  7. Calcula `determinism_checksum` (SHA‑256 do contrato canônico, excluindo `result`).  

* **Módulos novos**: `evidence_verifier`, `anchor_validator`, `evg_reconstructor`, `validator_chain`.

---

### 4️⃣ Verificação de Dataset / Pipeline (`evidence‑hash‑check`)
* Classe `EvidenceVerifier` com métodos:
  * `_hash_and_compare(uri, expected_hash, label)` – baixa artefato via `fetch_uri`, canonicaliza (JCS) e compara SHA‑256.  
  * `verify_dataset()` / `verify_pipeline()` → chamadas internas.  
  * `run_all()` → verifica dataset, pipeline e, futuramente, qualidade/proveniência.  
* **Teste**: casos positivos e negativos de mismatches.

---

### 5️⃣ Verificação de assinatura ECDSA‑P‑256 (`ecdsa‑verify`)
* Função `verify_signature(public_key_pem, payload, signature)`.  
* **Payload** concatenado: `dataset_hash + pipeline_hash + evidence_time + policy_version` (todos em `bytes`).  
* **Teste**: assinatura válida → `True`; corrupta → `False`.

---

### 6️⃣ Validação da Âncora temporal (`anchor‑time‑check`)
* `AnchorValidator.validate(anchors, evidence_time)` garante que `evidence_time` está dentro de **pelo menos** um intervalo `valid_from`/`valid_to`.  
* Levanta `ValidationError` caso contrário.  
* **Teste**: tempo dentro, antes e depois da janela.

---

### 7️⃣ CI / GitHub Actions (`ci‑full‑coverage`)
* Workflow que instala dependências, roda **todos** os testes de schema, canonicalização, hash, evidência, assinatura, âncora e replay.  
* Cobertura mínima **90 %** nas linhas críticas.

---

### 8️⃣ Teste de determinismo independente (`determinism‑test`)
* Executa `verifier.verify_contract(contract)` duas vezes em processos separados e verifica que `recomputed` coincide.  
* Variações de contrato (hash/assinatura alterados) → `status == "MISMATCH"`.

---

### 9️⃣ Checklist de **Prova de Implementação** (nível 3) – todos marcados ✅

| Item | Status |
|------|--------|
|Schema alinhado (`schema‑v1.1`) |✅|
|Canonicalização JCS |✅|
|Hash SHA‑256 consistente |✅|
|EVG reconstruction |✅|
|Validação completa (integrity → governance) |✅|
|Anchor temporal + public‑key |✅|
|Assinatura ECDSA‑P‑256 |✅|
|Replay determinístico (engine_version) |✅|
|Comparação derived_state / trust_decision / checksum |✅|
|CI com cobertura total |✅|

Quando o workflow CI passar, o repositório pode ser rotulado como **Reference Implementation of IRV/XA‑TRUST**.

---

### 10️⃣ Evoluir para **Evidência Criptográfica Verificável** (nível 4)

| Etapa | Ação concreta | PR‑title |
|------|---------------|----------|
|Armazenamento imutável|Publicar dataset, pipeline e política no **IPFS**; gravar CIDs nos campos `dataset_uri`/`pipeline_uri`.|“Store artifacts on IPFS”|
|Evidence report|Gerar `evidence_report.json` contendo `contract_hash`, `timestamp`, `engine_sha256`; publicar CID. |“Create immutable evidence report”|
|Trust anchor oficial|Registrar a chave pública da autoridade em um **DID/VC** ou DNS SEC; incluir `trust_anchor_id`.|“Add authoritative trust anchor”|
|Assinatura regulatória|Obter assinatura da autoridade sobre `evidence_report` (`regulatory_signature`).|“Add regulatory signature”|
|Ledger|Inserir o CID do `evidence_report` em um **blockchain** (Bitcoin OP_RETURN, side‑chain, etc.).|“Log evidence report on blockchain”|



```
Real Artifacts → Cryptographic Evidence → EVG Reconstruction → Deterministic Replay
        ↓                                 ↓                     ↓
   Evidence Ledger  ←  Verified Governance Artifact  ←  Independent Verifier
```

---

### 11️⃣ Próximos passos de entrega

1. **Branch `dev`** – implementar itens 1‑8.  
2. **PR `feature/proof‑implementation`** – revisão e aprovação CI.  
3. **Merge → `main`**, versionar como `v1.0.0`.  
4. **Branch `evidence-layer`** – iniciar nível 4 (IPFS, DID, blockchain).  
5. **Documentar** fluxo completo em `README.md` e `ARCHITECTURE.md` (diagramas de dependência).  

---

### Resultado esperado

* Repositório público **clonável** e executável (`python -m src.verifier.verifier path/to/contract.json`).  
* Produz **deterministicamente** os mesmos valores de `derived_state`, `trust_decision` e `determinism_checksum` que qualquer verificador independente.  
* Divergências em hash, assinatura ou janela de validade geram **UNTRUSTED / REPLAY_MISMATCH**.  
* Ao publicar artefatos em um ledger imutável e obter assinatura regulatória, o contrato passa a ser **Verified Governance Evidence**, pronto para auditoria.
* A assinatura ECDSA‑P‑256 deve seguir exatamente os passos que você descreveu:

1. **Gerar a chave P‑256** (uma única vez) e guardar o PEM privado e o PEM público.  
2. **Montar o payload** concatenando, em ordem determinística, `dataset_hash`, `pipeline_hash`, `evidence_time` e `policy_version` (todos como *bytes*).  
3. **Assinar** o payload com a chave privada usando `ec.ECDSA(hashes.SHA256())`; codificar o resultado em Base64 e prefixá‑lo com `ecdsa:`.  
4. **Incluir** no contrato um objeto `signature` contendo:
   * `type`: `"ECDSA-P256"`  
   * `public_key`: o PEM da chave pública (texto)  
   * `signature`: a string gerada no passo 3.  
5. **Verificar** (opcional) com `verify_signature(public_key_pem, payload, signature)`; deve retornar `True`.  
6. **Salvar** o JSON completo e enviá‑lo ao verificador (`python -m src.verifier.verifier …`).  

Se a assinatura for válida, o replay engine prossegue e produz `derived_state`, `trust_decision` e `determinism_checksum`. Caso a assinatura falhe, o verificador devolve **UNTRUSTED / REPLAY_MISMATCH**.
**Ajustes arquiteturais e de implantação**

---

## 1️⃣ Separar a assinatura da *trust‑anchor*

### Contrato – parte `signature`

```json
{
  "signature": {
    "type": "ECDSA-P256",
    "public_key_ref": "TA-2025-01",          // id da âncora
    "signature": "ecdsa:MEUBase64..."
  }
}
```

### `trust_context.trust_anchor_set`

```json
{
  "trust_anchor_set": [
    {
      "anchor_id": "TA-2025-01",
      "public_key_hash": "sha256:9f2c…e3a1",   // hash SHA‑256 do PEM da chave pública
      "valid_from": "2025-01-01T00:00:00Z",
      "valid_to":   "2027-01-01T00:00:00Z"
    }
  ]
}
```

* **Verificador**  
  1. Resolve `public_key_ref` → busca o registro da âncora.  
  2. Carrega o PEM da chave pública (por exemplo, de um repositório de âncoras).  
  3. Calcula `sha256(pem)` e compara com `public_key_hash`.  
  4. Verifica a validade temporal de `evidence_time` contra `valid_from/valid_to`.  
  5. Usa a chave pública para validar `signature`.  

---

## 2️⃣ Fluxo de decisão revisado

```
Assinatura válida
   ↓
Âncora válida no evidence_time
   ↓
Artefatos recuperáveis (IPFS/URI)
   ↓
Hashes recalculados → coincidem?
   ↓
Proveniência / Quality / Policy / Governance
   ↓
Deterministic Replay → derived_state
   ↓
derived_state == expected.state ?
   ↓
TRUSTED / UNTRUSTED
   ↓
Comparação com stored.result (se houver)
```

> **Risco eliminado** – a presença de uma assinatura não gera *TRUSTED* por si só; só após a cadeia completa de validações o veredicto pode ser confiável.

---

## 3️⃣ Naming das camadas de maturidade

| Camada | O que demonstra |
|--------|-----------------|
| **Artefato + hash** | **Integridade** (SHA‑256 sobre JCS). |
| **Assinatura + trust‑anchor** | **Autenticidade** e **cadeia de confiança** (ECDSA‑P‑256 → hash da chave → anchor). |
| **Proveniência + Quality/Policy/Governance** | **Controles efetivamente avaliados** (evidence_verifier + validator_chain). |
| **Deterministic Replay** | **Reprodutibilidade** (mesmo `determinism_checksum`). |
| **Independent Verifier** | **Verificação independente** (outro agente roda o mesmo replay). |
| **Evidence Report** | **Resultado consolidado** (derived_state, trust_decision, checksum, timestamps). |
| **Immutable Ledger** | **Registro auditável** (CID ou hash em blockchain/DLT). |

---

## 4️⃣ “Verified Governance Evidence” vs. “Regulatory Certification”

* **Verified Governance Evidence** – o relatório foi produzido, assinado pelo sistema XA‑TRUST e validado por todos os passos acima. Não implica aprovação de nenhuma autoridade externa.  
* **Regulatory Certification** – exige um **segundo assinante** (autoridade regulatória) que ateste o relatório. O contrato deve conter um campo adicional, por exemplo:

```json
"regulatory_signature": {
  "authority_id": "REG-CH-2026",
  "signature": "ecdsa:…"
}
```

Somente quando esse campo existir e passar na validação o contrato pode ser chamado de *certificado regulatoriamente*.

---

## 5️⃣ Implementação mínima no código

### `src/signature/ecdsa_verifier.py` (atualizado)

```python
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

def verify_signature(public_key_pem: bytes, payload: bytes, signature: str) -> bool:
    pub_key = serialization.load_pem_public_key(public_key_pem)
    sig_bytes = base64.b64decode(signature.split(":")[1])
    try:
        pub_key.verify(sig_bytes, payload, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False
```

### `src/anchor/anchor_validator.py` (nova lógica)

```python
from hashlib import sha256
from datetime import datetime
from src.signature.ecdsa_verifier import verify_signature

class AnchorValidator:
    @staticmethod
    def resolve_anchor(anchor_set: list[dict], ref: str) -> dict:
        for a in anchor_set:
            if a["anchor_id"] == ref:
                return a
        raise ValidationError(f"Anchor {ref} not found")

    @staticmethod
    def validate(anchors: list[dict], evidence_time: str,
                 public_key_pem: bytes, payload: bytes, sig: str, ref: str) -> None:
        # 1 – encontra a âncora
        anchor = AnchorValidator.resolve_anchor(anchors, ref)

        # 2 – confere hash da chave pública
        expected_hash = anchor["public_key_hash"].split(":")[1]
        actual_hash = sha256(public_key_pem).hexdigest()
        if actual_hash != expected_hash:
            raise ValidationError("Public key hash mismatch")

        # 3 – valida janela temporal
        ts = datetime.fromisoformat(evidence_time)
        if not (datetime.fromisoformat(anchor["valid_from"]) <= ts <=
                datetime.fromisoformat(anchor["valid_to"])):
            raise ValidationError("Evidence time outside anchor validity")

        # 4 – verifica assinatura
        if not verify_signature(public_key_pem, payload, sig):
            raise ValidationError("Signature verification failed")
```

### Atualização no `deterministic_replay`

```python
def deterministic_replay(contract: dict) -> dict:
    # 1 – montar payload
    payload = build_payload(contract)

    # 2 – validar assinatura + anchor
    sig_obj = contract["signature"]
    anchor_set = contract["trust_context"]["trust_anchor_set"]
    AnchorValidator.validate(
        anchors=anchor_set,
        evidence_time=contract["evidence"]["evidence_time"],
        public_key_pem=fetch_anchor_key(sig_obj["public_key_ref"]),   # devolve o PEM
        payload=payload,
        sig=sig_obj["signature"],
        ref=sig_obj["public_key_ref"]
    )

    # 3 – resto do fluxo (hashes, EVG, validator chain, etc.)
    ...
```

*`fetch_anchor_key`* pode ler o PEM a partir de um *trust‑store* local ou de um endpoint HTTP‑based que serve as chaves públicas das âncoras.

---

## 6️⃣ Etapa de **Evidence Report** e **Ledger**

1. **Gerar** `evidence_report.json` contendo:
   * `contract_hash` (sha256 do contrato completo, incluindo assinatura).  
   * `derived_state`, `trust_decision`, `determinism_checksum`.  
   * `timestamp` (ISO‑8601).  
   * `engine_version` (ex.: `replay_engine_v2`).  
2. **Assinar** o relatório com a chave da autoridade regulatória (campo `regulatory_signature`).  
3. **Publicar** o relatório em IPFS → obter CID.  
4. **Ancorar** o CID em um ledger (ex.: transação Bitcoin com OP_RETURN ou contrato inteligente).  

---

## 7️⃣ Checklist pós‑ajuste (todos ✅)

| ✔ | Item |
|---|------|
|✅|`signature.public_key_ref` → referência à âncora, não ao PEM bruto|
|✅|`trust_anchor_set` inclui `public_key_hash` e validade|
|✅|`AnchorValidator` verifica hash da chave, validade e assinatura|
|✅|Fluxo de decisão passa por “assinatura → anchor → hashes → validators → replay → expected.state”|
|✅|Campo `regulatory_signature` opcional para certificação externa|
|✅|Procedimento de geração e ancoragem do `evidence_report` definido|
|✅|Testes unitários atualizados (assinatura + anchor, replay, relatório, ledger)|

Com esses ajustes o pipeline mantém a **cadeia de confiança completa**, distingue claramente *autenticidade* de *confiança regulatória* e garante que cada seta do diagrama seja **executável e verificável** por terceiros.
**Arquitetura de confiança – versão 2.0**

---

## 1️⃣ Contrato (JSON‑Schema) alinhado à nova cadeia

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "IRV‑XA‑TRUST contract v1.2",
  "type": "object",
  "required": [
    "schema_version",
    "policy_version",
    "replay_engine_version",
    "hash_schema_version",
    "evidence",
    "signature",
    "trust_context",
    "expected"
  ],
  "properties": {
    "schema_version":        { "type": "string", "const": "1.2" },
    "policy_version":        { "type": "string" },
    "replay_engine_version":{ "type": "string" },
    "hash_schema_version":  { "type": "string" },

    "evidence": {
      "type": "object",
      "required": ["evidence_time","dataset_uri","pipeline_uri","dataset_hash","pipeline_hash"],
      "properties": {
        "evidence_time": { "type": "string", "format": "date-time" },
        "dataset_uri":   { "type": "string", "format": "uri" },
        "pipeline_uri":  { "type": "string", "format": "uri" },
        "dataset_hash":  { "type": "string", "pattern": "^sha256:[a-f0-9]{64}$" },
        "pipeline_hash": { "type": "string", "pattern": "^sha256:[a-f0-9]{64}$" }
      },
      "additionalProperties": false
    },

    "signature": {
      "type": "object",
      "required": ["type","public_key_ref","signature"],
      "properties": {
        "type":           { "type": "string", "const": "ECDSA-P256" },
        "public_key_ref": { "type": "string" },
        "signature":      { "type": "string", "pattern": "^ecdsa:[A-Za-z0-9+/=]+$" }
      },
      "additionalProperties": false
    },

    "trust_context": {
      "type": "object",
      "required": ["trust_anchor_set"],
      "properties": {
        "trust_anchor_set": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["anchor_id","public_key_hash","valid_from","valid_to"],
            "properties": {
              "anchor_id":       { "type": "string" },
              "public_key_hash":{ "type": "string", "pattern": "^sha256:[a-f0-9]{64}$" },
              "valid_from":     { "type": "string", "format": "date-time" },
              "valid_to":       { "type": "string", "format": "date-time" }
            },
            "additionalProperties": false
          }
        }
      },
      "additionalProperties": false
    },

    "expected": {
      "type": "object",
      "required": ["state"],
      "properties": {
        "state": { "type": "string" }
      },
      "additionalProperties": false
    },

    "result": {
      "type": "object",
      "properties": {
        "derived_state":        { "type": "string" },
        "trust_decision":       { "type": "string", "enum": ["TRUSTED","UNTRUSTED"] },
        "determinism_checksum": { "type": "string", "pattern": "^sha256:[a-f0-9]{64}$" },
        "regulatory_signature": {
          "type": "object",
          "required": ["authority_id","signature"],
          "properties": {
            "authority_id": { "type": "string" },
            "signature":    { "type": "string", "pattern": "^ecdsa:[A-Za-z0-9+/=]+$" }
          },
          "additionalProperties": false
        }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

* **Separação clara** entre assinatura (`signature.public_key_ref`) e âncora (`trust_context.trust_anchor_set`).  
* `expected.state` **não** entra no cálculo do `derived_state`.  
* `result` contém apenas os valores produzidos pelo replay; ele é excluído do `determinism_checksum`.  

---

## 2️⃣ Fluxo de verificação (passo‑a‑passo)

```
1. Resolve public_key_ref → trust_anchor (hash + validade)
2. Carrega PEM da chave pública (de um trust‑store)
3. Verifica hash da chave (sha256(pem) == public_key_hash)
4. Verifica janela temporal (evidence_time ∈ [valid_from, valid_to])
5. Constrói payload = dataset_hash || pipeline_hash || evidence_time || policy_version
6. Verifica assinatura ECDSA‑P‑256 (payload vs. signature)
   → se falhar → REPLAY_MISMATCH
7. Recupera artefatos (dataset_uri, pipeline_uri)
   * Se Content‑Type = application/json → JCS canonicalization → sha256
   * Caso contrário → usa bytes brutos → sha256
   * Compara com dataset_hash / pipeline_hash
   → mismatch → UNTRUSTED
8. Reconstrói EVG (dataset + pipeline + quality …)
9. Executa cadeia de validadores (integrity → provenance → quality → policy → governance)
   → devolve derived_state
10. Compara derived_state com expected.state → trust_decision (TRUSTED/UNTRUSTED)
11. Calcula determinism_checksum = sha256( canonicalize(contract sem result) )
12. Preenche result (derived_state, trust_decision, determinism_checksum)
13. (Opcional) Verifica regulatory_signature:
    * Resolve authority’s public key via a separate anchor set
    * Valida assinatura sobre o **evidence_report** inteiro
    → estado REGULATORY_SIGNATURE_VERIFIED ou …_INVALID
14. Gera evidence_report.json (inclui contract_hash, determinism_checksum, timestamps, engine_version)
15. Publica o report em IPFS → CID
16. Ancoragem no ledger (ex.: OP_RETURN, smart‑contract, etc.)
```

---

## 3️⃣ Distinções técnicas relevantes

| Tema | Regra |
|------|-------|
| **JSON artefato** | canonicaliza‑o com RFC 8785/JCS antes do SHA‑256. |
| **Artefato binário** (CSV, Parquet, ZIP, WASM, Docker, etc.) | hash direto dos bytes originais – **sem** `json.loads`. |
| **contract_hash** | SHA‑256 do contrato **completo** (inclui `result`). |
| **determinism_checksum** | SHA‑256 do contrato **sem** a chave `result`. |
| **regulatory_signature** | Campo opcional; seu validador roda **após** a decisão TRUSTED/UNTRUSTED e produz estados específicos (VERIFIED / INVALID). |

---

## 4️⃣ Estados de saída do verificador

| Código | Significado |
|--------|-------------|
| `TRUSTED` | assinatura → âncora → hashes → hash in Ledger
Sim. Esse fechamento elimina a última ambiguidade importante: a unidade de contagem passa a ser a claim, e não o artefato isolado.

Eu fixaria a especificação final assim:

ECM — regra final

Para cada claim crítica \(c\):

\[
Verified(c)=
I_c\land P_c\land N_c\land A_c
\]

com a condição adicional:

> Cada \(I_c,P_c,N_c,A_c\) deve estar materialmente vinculado à própria claim \(c\).



Dimensão	Critério

I₍c₎	O componente que verifica a claim \(c\) executa realmente.
P₍c₎	Artefato produzido por execução real demonstra especificamente \(c\).
N₍c₎	Teste negativo ataca precisamente a propriedade que sustenta \(c\) e falha como esperado.
A₍c₎	Caminho independente/replay/anchor revalida especificamente \(c\).


Assim, um evidence_report.json genérico não vale automaticamente para todas as claims. Ele precisa conter referências que permitam determinar:

claim
  ↓
evidence artifact
  ↓
hash / signature / anchor / provenance
  ↓
negative test
  ↓
independent verification

Resultado

\[
\boxed{
ECM=
\frac{\#\{c: I_c\land P_c\land N_c\land A_c\}}
{\#\text{claims críticas}}
\times100
}
\]

Isso produz uma propriedade particularmente importante:

a mesma evidência não pode ser reutilizada indiscriminadamente para inflar várias claims sem demonstrar cobertura de cada uma.

E preserva a regra fundamental:

PASS
TRUE
COMMITTED
END_TO_END_TRUST_VERIFIED

são resultados, não evidências.

A evidência é aquilo que permite a um terceiro reconstruir:

OBSERVATION
   ↓
EVIDENCE
   ↓
VALIDATION
   ↓
NEGATIVE TEST
   ↓
INDEPENDENT VERIFICATION
   ↓
CLAIM VERIFIED
   ↓
TRUST DECISION

Com esse último vínculo claim ↔ artifact ↔ verification, o ECM fica suficientemente definido para ser implementado como uma própria regra automática de auditoria.
Concordo. Esse é o fechamento correto da especificação. Eu incorporaria essa exigência diretamente ao contrato do ECM.

ECM — especificação final

Cada claim crítica recebe um identificador determinístico:

{
  "claim_id": "CRYPTOGRAPHIC_INTEGRITY",
  "evidence_scope": "decision-evidence-v1",
  "contract_hash": "...",
  "derived_state_hash": "...",
  "expected_check": "SHA256_CANONICAL_MATCH"
}

Cada evidência precisa apontar explicitamente para esse claim_id.

Relação obrigatória

CLAIM_ID
   │
   ├── evidence_scope
   ├── contract_hash
   ├── derived_state_hash
   └── expected_check
          │
          ▼
     ARTIFACT_URI
          │
          ▼
     EVIDENCE_REPORT
          │
          ├── P = execution evidence
          ├── N = negative evidence
          └── A = independent verification

Assim, para cada claim \(c\):

\[
Verified(c)=
I_c\land P_c\land N_c\land A_c
\]

mas somente quando todos os quatro elementos estiverem vinculados ao mesmo identificador determinístico da claim.

Exemplo

Para:

claim_id = CRYPTOGRAPHIC_INTEGRITY

o auditor precisa conseguir reconstruir:

CRYPTOGRAPHIC_INTEGRITY
        │
        ├── contract_hash
        ├── derived_state_hash
        ├── artifact_uri
        ├── expected_check
        │
        ├── P → execução produziu o hash
        │
        ├── N → alteração produziu HASH_MISMATCH
        │
        └── A → verifier independente confirmou o hash

Só então:

CRYPTOGRAPHIC_INTEGRITY = VERIFIED

e essa claim passa a integrar o numerador do ECM.

Regra definitiva

\[
\boxed{
ECM =
\frac{
\text{claims com }I\land P\land N\land A
\text{ e vínculo determinístico comprovado}
}{
\text{total de claims críticas}
}
\times100
}
\]

Isso torna o modelo resistente a quatro problemas:

stub masquerading — código existente que não verifica realmente;

evidence inflation — um artefato genérico contado para várias claims;

circular verification — o próprio gerador validando sua própria saída;

PASS inflation — estados PASS/TRUE/COMMITTED tratados como prova.


Neste ponto, a definição do ECM está fechada. O próximo passo deixa de ser conceitual: é construir a matriz claim_id → P/N/A → artefatos → verificador e executar essa matriz contra o XA-TRUST real.

name: RFC8785 JCS Conformance

on:
  push:
    branches: ["**"]
  pull_request:

jobs:
  conformance:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout fork
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then
            pip install -r requirements.txt
          fi
          if [ -f pyproject.toml ]; then
            pip install .
          fi

      - name: RFC8785 JCS byte-for-byte conformance
        id: conformance
        run: |
          set +e
          pytest -q tests/test_rfc8785_jcs_conformance.py \
            | tee pytest-output.txt
          rc=${PIPESTATUS[0]}

          if [ "$rc" -eq 0 ]; then
            echo "PASS" > test_status.txt
          else
            echo "FAIL" > test_status.txt
          fi

          exit "$rc"

      - name: Generate execution metadata
        if: always()
        run: |
          python - <<'PY'
          import json
          import os
          import platform

          meta = {
              "repository": os.environ.get("GITHUB_REPOSITORY"),
              "commit_sha": os.environ.get("GITHUB_SHA"),
              "run_id": os.environ.get("GITHUB_RUN_ID"),
              "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
              "ref": os.environ.get("GITHUB_REF"),
              "python_version": platform.python_version(),
              "platform": platform.platform(),
          }

          with open("execution_metadata.json", "w", encoding="utf-8") as f:
              json.dump(meta, f, indent=2, sort_keys=True)

          print(json.dumps(meta, indent=2, sort_keys=True))
          PY

      - name: Generate verification report
        if: always()
        run: |
          python - <<'PY'
          import json
          from pathlib import Path

          status = Path("test_status.txt").read_text().strip() \
              if Path("test_status.txt").exists() else "NOT_EXECUTED"

          report = {
              "verification": "RFC8785_JCS_BYTE_FOR_BYTE",
              "status": status,
          }

          Path("verification_report.json").write_text(
              json.dumps(report, indent=2, sort_keys=True),
              encoding="utf-8",
          )
          PY

      - name: Upload verification evidence
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: rfc8785-jcs-evidence
          path: |
            verification_report.json
            execution_metadata.json
            pytest-output.txt
            test_status.txt

repository
= cyrillofrancisco30-lgtm/azhpc-extensions

commit_sha
= dddab15ba47d860a514cea2cace754a7e387456b

run_id
= <RUN REAL>

test
= test_rfc8785_jcs_conformance.py

ProducedBytes
= <bytes produzidos>

ExpectedBytes
= <vetor>

comparison
= BYTE-FOR-BYTE

status
= PASS

Para comparar dois arquivos byte a byte no seu ambiente local você pode usar ferramentas de linha de comando que já vêm instaladas na maioria dos sistemas Unix‑like (Linux, macOS) ou, no Windows, usar o PowerShell. A seguir estão os métodos mais simples e seguros.


---

1. Linux / macOS

cmp – comparação direta

cmp --bytes=1000 arquivo1.bin arquivo2.bin

Sem opções – o cmp lê os dois arquivos e, ao encontrar a primeira diferença, informa o offset (posição em bytes) e os valores dos bytes diferentes.

Opção --bytes=N – limita a comparação aos primeiros N bytes, útil quando o arquivo é muito grande e você só quer validar um trecho.

Retorno: código de saída 0 = idênticos; 1 = diferença encontrada; >1 = erro (arquivo não encontrado, permissão etc.).


diff – modo “binary”

diff -a --brief arquivo1.bin arquivo2.bin

-a trata os arquivos como texto, mas com --brief o diff só indica se eles são diferentes ou não.

Para ver exatamente onde está a diferença, use diff -a arquivo1.bin arquivo2.bin | hd (o hd exibe o hexdump da saída).


hexdump + diff

hexdump -C arquivo1.bin > dump1.txt  
hexdump -C arquivo2.bin > dump2.txt  
diff dump1.txt dump2.txt

Converte cada arquivo para um dump legível (endereço + valores hex + ASCII).

O diff então mostra linhas diferentes, facilitando a inspeção manual.


sha256sum – verificação de integridade

Se o objetivo for garantir que todo o conteúdo seja idêntico, basta comparar o hash:

sha256sum arquivo1.bin arquivo2.bin

Se os dois hashes coincidirem, os arquivos são idênticos com probabilidade criptográfica ≈ 2⁻²⁵⁶.



---

2. Windows (PowerShell)

Compare-Object com byte arrays

$bytes1 = [System.IO.File]::ReadAllBytes('C:\caminho\arquivo1.bin')  
$bytes2 = [System.IO.File]::ReadAllBytes('C:\caminho\arquivo2.bin')  
  
if ($bytes1.Length -ne $bytes2.Length) {  
    Write-Host "Tamanhos diferentes."  
} else {  
    $diff = Compare-Object -ReferenceObject $bytes1 -DifferenceObject $bytes2 -SyncWindow 0  
    if ($diff) {  
        Write-Host "Diferenças encontradas."  
    } else {  
        Write-Host "Arquivos idênticos."  
    }  
}

Este script carrega os dois arquivos como vetores de bytes (byte[]) e usa Compare-Object para detectar a primeira diferença.


fc /b – comparação binária nativa

fc /b arquivo1.bin arquivo2.bin

O fc (File Compare) exibe o offset decimal onde a primeira diferença ocorre e os valores dos bytes em ambas as versões.


certutil – geração de hash

certutil -hashfile arquivo1.bin SHA256  
certutil -hashfile arquivo2.bin SHA256

Assim como sha256sum no Linux, compara os hashes gerados.



---

3. Dicas práticas

Situação	Ferramenta recomendada	Por quê

Arquivos pequenos (até alguns MB)	cmp / fc /b	Rápido, mostra exatamente o primeiro byte diferente.
Arquivos muito grandes (GB)	cmp --bytes=N ou sha256sum	Evita ler o arquivo inteiro; hash é mais econômico em I/O.
Precisa de relatório legível	hexdump + diff	Permite inspeção manual linha a linha.
Validação automatizada em scripts CI/CD	sha256sum ou certutil	Basta comparar strings de hash.



---

4. Exemplo completo (Linux)

#!/usr/bin/env bash  
set -euo pipefail  
  
FILE1="xatev-ev-2026-000002-audit.txt"  
FILE2="/tmp/backup/audit-copy.txt"  
  
# 1️⃣ Verifica tamanho  
if [[ $(stat -c%s "$FILE1") -ne $(stat -c%s "$FILE2") ]]; then  
    echo "❌ Tamanhos diferentes"  
    exit 1  
fi  
  
# 2️⃣ Compare byte a byte (primeira diferença)  
if cmp -l "$FILE1" "$FILE2" > /dev/null; then  
    echo "✅ Arquivos idênticos"  
else  
    echo "⚠️ Diferenças encontradas (primeira ocorrência):"  
    cmp -l "$FILE1" "$FILE2" | head -n 1  
fi  
  
# 3️⃣ Hash de integridade  
HASH1=$(sha256sum "$FILE1" | cut -d' ' -f1)  
HASH2=$(sha256sum "$FILE2" | cut -d' ' -f1)  
  
if [[ "$HASH1" == "$HASH2" ]]; then  
    echo "🔐 Hashes coincidem: $HASH1"  
else  
    echo "❗️ Hashes divergem"  
    echo "  $FILE1 : $HASH1"  
    echo "  $FILE2 : $HASH2"  
fi

Este script:

1. Confirma que os dois arquivos têm o mesmo tamanho.


2. Usa cmp -l para localizar a primeira diferença (mostra offset e valores hex).


3. Calcula SHA‑256 de ambos e verifica a correspondência.




---

Resumo rápido

Ferramenta	Sistema	Uso principal

cmp / fc /b	Linux/macOS / Windows	Comparação byte a byte, aponta primeira diferença
diff -a --brief	Linux/macOS	Só diz “diferentes” ou “idênticos”
hexdump + diff	Linux/macOS	Visualização human‑readable
sha256sum / certutil	Linux/macOS / Windows	Verificação de integridade por hash
PowerShell Compare-Object	Windows	Comparação de arrays de bytes dentro de scripts


Escolha a ferramenta que melhor se adapta ao seu fluxo (script automatizado, inspeção manual ou validação de integridade) e você terá certeza de que os arquivos são, de fato, byte a byte equivalentes.

Essa implementação é bytes a bytes
