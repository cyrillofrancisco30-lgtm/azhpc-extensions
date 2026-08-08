

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
