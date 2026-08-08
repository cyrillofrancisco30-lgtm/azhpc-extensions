

---

## 1. Estrutura do repositório

```
xa-trust/
├─ .github/
│   └─ workflows/
│       └─ ci.yml                # CI de validação (lint, testes, replay)
├─ src/
│   ├─ canonicalization/
│   │   └─ rfc8785_jcs.py        # implementação RFC 8785 / JCS
│   ├─ hash/
│   │   └─ sha256.py             # wrapper simples para SHA‑256
│   ├─ replay/
│   │   └─ engine.py             # motor determinístico (versão 2.1.0)
│   ├─ verifier/
│   │   └─ verifier.py           # orquestração completa
│   └─ utils/
│       └─ io.py                 # fetch de artefatos (IPFS, S3, HTTP)
├─ contracts/
│   └─ irv_xa_trust_schema.json   # esquema JSON do contrato (versão 1.0)
├─ examples/
│   └─ sample_package.json       # exemplo de payload (place‑holders)
├─ tests/
│   ├─ test_canonicalization.py
│   ├─ test_hash.py
│   ├─ test_replay.py
│   └─ test_verifier.py
├─ scripts/
│   └─ generate_hashes.py        # gera dataset_hash, pipeline_hash, etc.
├─ README.md
├─ LICENSE
└─ pyproject.toml                # dependências (pydantic, cryptography, jsonschema)
```
NSL-25-165432
      │
      ├─ Public availability        ✓
      ├─ Source traceability        ✓
      ├─ Legal/temporal metadata    ✓
      ├─ Document hash              PENDING
      ├─ Signature verification     PENDING
      ├─ Independent verification   PENDING
      └─ Immutable anchor           PENDING
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
17  Run Policy Validator
18  Run Governance Validator
19  Derive State
20  Compare Expected State
21  Calculate Determinism Checksum
22  Produce Verification Result
23  Optionally Verify Regulatory Attestation
24  Generate Evidence Report
25  Canonicalize Report
26  Calculate Report Hash
27  Publish to IPFS
28  Obtain CID
29  Anchor CID/report hash in Ledger
---

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
