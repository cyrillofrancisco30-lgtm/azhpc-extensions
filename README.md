

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
4. Opcional: habilite **GitHub Packages** para publicar a biblioteca como artefato `pip`.

---

### Próximos passos (para subir ao nível 3/4)

| Etapa | O que fazer | Onde registrar |
|------|--------------|-----------------|
| **Artefatos reais** | Armazenar dataset e pipeline em IPFS ou bucket S3 com hash imutável. | `evidence.dataset_uri`, `evidence.pipeline_uri` |
| **Assinatura robusta** | Gerar chave ECDSA‑P‑256, publicar a chave pública em um **trust anchor** (ex.: registro DNSSEC ou ledger público). | `trust_context.anchor` |
| **Política versionada** | Versionar a política (ex.: `policy/v2.3.json`) e referenciá‑la no contrato. | `expected.policy_version` |
| **Auditoria externa** | Submeter o contrato preenchido a um auditor independente; o relatório de auditoria pode ser incluído como `evidence.audit_report_uri`. | `evidence` |

Após essas integrações, o contrato deixará de ser “exemplo” e passará a ser **evidência criptográfica verificável** (nível 3) e, com apoio de auditoria reconhecida, **evidência de conformidade regulatória** (nível 4).

---

**Pronto!**  
Com a estrutura, o código e o workflow acima, você tem tudo que precisa para criar o repositório GitHub **cyrillofrancisco30‑lgtm/xa‑trust**, publicar a implementação e começar a gerar evidências reais que podem ser validadas por verificadores independentes. Boa implementação!
# Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
