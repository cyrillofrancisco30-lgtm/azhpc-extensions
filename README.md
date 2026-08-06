XA TRUST PLATFORM Governance 

---

## 1. Conformance Runner (CLI)

1. **Criar binário** `xa-trust conform` que:
   * Carrega `certification/api‑contract.json`.
   * Lê **todos** os *golden‑tests* (`golden-tests/trusted/*.json`) e *determinism‑tests* (`golden-tests/determinism/*.json`).
   * Executa o motor de replay (`STRICT_EVG_REPLAY`) contra cada *EvidencePackage* usando o **TrustContext** e a **Policy** indicados.
   * Gera, para cada teste, um **replay‑report** em `certification/replay-reports/` contendo:
     ```json
     {
       "testId":"…",
       "engineVersion":"2.1.0",
       "schemaBinding":"xa-trust-irv@2.1.0",
       "inputDigest":"sha256:…",
       "evgHash":"sha256:…",
       "determinismChecksum":"sha256:…",
       "decision":"TRUSTED",
       "status":"PASS"
     }
     ```
   * Depois de rodar todos os testes, imprime um resumo JSON:

     ```json
     {
       "suite":"v2.1.0",
       "tests":2,
       "passed":2,
       "failed":0,
       "level":"TRUST_CERTIFIED"
     }
     ```

2. **Integração ao CI** (GitHub Actions, GitLab CI, etc.) – o job deve falhar se o resumo não for exatamente o acima.

---

## 2. Engine Identity

1. **Calcular o tree‑hash** do repositório:
   ```bash
   git ls-tree -r HEAD | sha256sum | awk '{print $1}'
   ```
2. **Criar `certification/engine-identity.json`**:

   ```json
   {
     "implementation":"xa-trust-irv",
     "version":"2.1.0",
     "engine":"STRICT_EVG_REPLAY",
     "source_digest":"sha256:<tree‑hash>"
   }
   ```

3. **Validar** que o hash corresponde ao commit que será tagueado (use `git rev-parse HEAD` para conferir).

---

## 3. Ledger Anchor completo

Atualize todos os arquivos em `certification/ledger-anchors/` para o schema definitivo:

```json
{
  "anchor_version":"1.0",
  "event_hash":"sha256:<event‑hash>",
  "merkle_root":"sha256:<merkle‑root>",
  "algorithm":"SHA-256",
  "status":"ANCHORED"
}
```

- `event_hash` = `determinism_checksum` do DEP.
- `merkle_root` pode ser um hash simples da lista de eventos (para a prova de integridade de cadeia).

---

## 4. Prova de não‑determinismo (DT‑001)

1. Execute duas vezes a mesma sequência de `transition(state, ev)` com o mesmo objeto `Evidence`.
2. Calcule o hash da lista de eventos (`sha256(json.dumps(ledger, sort_keys=True))`).
3. Salve em `certification/determinism-proofs/dt-001-proof.json`:

   ```json
   {
     "execution1":"sha256:<hash1>",
     "execution2":"sha256:<hash2>",
     "match":true
   }
   ```

Este arquivo será consumido pelo Conformance Runner como parte do teste de determinismo.

---

## 5. Atualizar o **Decision Evidence Package (DEP)**

Quando o estado final for `TRUST_APPROVED`, gere um `trust-decision.json` que inclua:

```json
{
  "trust_decision":"TRUSTED",
  "evg_hash":"sha256:<evg_hash>",
  "determinism_checksum":"sha256:<checksum>",
  "replay_mode":"STRICT_EVG_REPLAY",
  "ledger_anchor":{
    "status":"ANCHORED",
    "event_hash":"sha256:<checksum>"
  },
  "schema_status":"FROZEN"
}
```

Copie‑o para `certification/implementation-metadata.json` (ou mantenha‑o separado; o Conformance Runner apenas verifica a consistência entre eles).

---

## 6. CI/CD Pipeline completo (exemplo **GitHub Actions**)

```yaml
name: XA‑TRUST CI

on:
  push:
    branches: [main]

jobs:
  freeze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Rust
        uses: actions/setup-rust@v1
        with:
          rust-version: stable

      - name: Build & test
        run: |
          cargo test --quiet
          cargo run --release -- \
            --evidence examples/evidence.json \
            --context  examples/trust-context.json \
            --policy   examples/policy.yaml

      - name: Generate ledger events
        env:
          EVENT_FILE: certification/replay-reports/run-${{ github.run_id }}.json
        run: |
          python demo.py > $EVENT_FILE   # demo.py contém a máquina de estados

      - name: Engine identity
        run: |
          TREE=$(git ls-tree -r HEAD | sha256sum | awk '{print $1}')
          cat > certification/engine-identity.json <<EOF
          {
            "implementation":"xa-trust-irv",
            "version":"2.1.0",
            "engine":"STRICT_EVG_REPLAY",
            "source_digest":"sha256:${TREE}"
          }
          EOF

      - name: Determinism proof
        run: |
          python -c "import determinism_test; determinism_test()"   # gera dt-001-proof.json

      - name: Conformance run
        run: |
          ./target/release/xa-trust conform --suite golden-tests

      - name: Tag frozen (only on success)
        if: success()
        env:
          GIT_AUTHOR_NAME: github-actions
          GIT_AUTHOR_EMAIL: actions@github.com
        run: |
          git config user.name "$GIT_AUTHOR_NAME"
          git config user.email "$GIT_AUTHOR_EMAIL"
          git tag -a v2.1.0-frozen -m "Frozen Reference Implementation – CI"
          git push origin v2.1.0-frozen
```

*Os scripts `demo.py` e `determinism_test.py` devem conter a lógica de máquina de estados e o teste de não‑determinismo mostrados na sua mensagem anterior.*

---

## 7. Verificação final antes da tag

| ✔︎ | Checklist |
|---|-----------|
| 1 | `cargo test` → PASS |
| 2 | `xa-trust conform --suite golden-tests` → JSON com `tests:2`, `passed:2`, `failed:0`, `level:"TRUST_CERTIFIED"` |
| 3 | `engine-identity.json` contém o **tree‑hash** do commit que será tagueado |
| 4 | Todos os **ledger‑anchors** têm `anchor_version`, `algorithm` e prefixo `sha256:` |
| 5 | **Replay‑reports** e **determinism‑proofs** seguem os schemas acima |
| 6 | CI bloqueia merge sem passar nos itens 1‑2 |
| 7 | Tag `v2.1.0-frozen` criada 
