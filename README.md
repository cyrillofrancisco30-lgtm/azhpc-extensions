O material consolida uma definição suficientemente precisa da claim `JCS_BYTE_FOR_BYTE_CONFORMANCE` para avançarmos à especificação executável do XA-TRUST / ECM.

Minha recomendação é congelar G1 — Governança como baseline documental da claim, sem confundir esse congelamento com aprovação técnica ou execução.

### XA-TRUST / ECM — Baseline G1

Escopo definido documentalmente

| Campo       | Definição                        |
| ----------- | -------------------------------- |
| Claim       | JCS_BYTE_FOR_BYTE_CONFORMANCE    |
| Escopo      | LOCAL_VECTORS_ONLY               |
| Referência  | RFC 8785                         |
| Entrada     | tests/jcs/vectors.json           |
| Executor    | tools/jcs_ecm/run_vectors.py     |
| Evidência   | test_execution.json              |
| Identidade  | execution_metadata.json          |
| Integridade | artifact_hashes.json             |
| Verificador | tools/jcs_ecm/verify_evidence.py |
| Resultado   | verification_result.json         |

### 1\. Contrato de decisão

É importante formalizar a independência entre os três resultados:

```yaml
execution:
  result:
    - PASS
    - FAIL
    - INCOMPLETE

verification:
  result:
    - VERIFIED
    - NOT_VERIFIED
    - VERIFICATION_FAILED

ecm:
  decision:
    - PROMOTE
    - HOLD
    - REJECT
```

A interpretação é:

* `PASS`: todos os vetores obrigatórios executados passaram.

* `VERIFIED`: o pacote e seus vínculos foram confirmados pelo verificador.

* `PROMOTE`: a governança autorizou a claim dentro do escopo declarado.

Nenhum desses estados é herdado automaticamente pelo estágio seguinte.

### 2\. Condições obrigatórias de G4

O verificador independente deve:

* Validar o schema do pacote.

* Recalcular o SHA-256 dos vetores.

* Conferir a identidade real do workflow e da execução.

* Recalcular hashes e tamanhos dos artefatos.

* Conferir as contagens de vetores carregados, executados, aprovados e reprovados.

* Verificar cada resultado contra os bytes esperados preservados.

* Rejeitar divergências entre `head_sha`, commit avaliado e artefato testado.

* Produzir um relatório próprio, com versão do verificador e da política ECM.

Um manifesto produzido pelo executor não é suficiente para provar sua própria integridade. O G4 precisa recalcular os valores a partir dos artefatos recebidos.

### 3\. Regra de promoção

G5 = G1 \\land G2 \\land G3 \\land G4

Com a condição de que todos os gates sejam satisfeitos e que a política aplicável autorize a promoção.

| Ocorrência                        | Decisão |
| --------------------------------- | ------- |
| Vetor divergente                  | REJECT  |
| Execução incompleta               | HOLD    |
| Evidência ausente                 | HOLD    |
| Integridade inválida              | REJECT  |
| Verificação independente pendente | HOLD    |
| Todos os critérios satisfeitos    | PROMOTE |

### 4\. Estado documental consolidado

| Estágio                  | Estado sustentado pelo material |
| ------------------------ | ------------------------------- |
| G1 — Governança          | DOCUMENTED                      |
| G2 — Implementação       | NOT ESTABLISHED                 |
| G3 — Execução            | NOT ESTABLISHED                 |
| G4 — Verificação         | NOT ESTABLISHED                 |
| G5 — Homologação técnica | NOT AUTHORIZED                  |

Limite da claim: a promoção, quando sustentada, será restrita aos vetores locais identificados por hash, versão e escopo. constituirá certificação universal da RFC 8785 nem aprovação regulatória.

### 5\. Próxima entrega técnica

O artefato central a produzir é `tools/jcs_ecm/verify_evidence.py`, acompanhado de:

* `schemas/test-execution.schema.json`;

* `schemas/execution-metadata.schema.json`;

* `schemas/artifact-hashes.schema.json`;

* `schemas/verification-result.schema.json`;

* testes negativos para assinatura ausente/inválida, hash divergente, commit incorreto, vetor omitido e tentativa de promoção com evidência incompleta;

* workflow produtor e workflow verificador separados.

A implementação deve partir dos arquivos reais do repositório. Sem acesso ao conteúdo desses arquivos, não seria correto afirmar compatibilidade com interfaces ou caminhos ainda não confirmados.

Decisão recomendada: preservar esta definição como baseline G1 e avançar para a implementação verificável de G2, mantendo G3, G4 e G5 bloqueados até existirem evidências concretas.


# Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.


disparar workflow 


This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
