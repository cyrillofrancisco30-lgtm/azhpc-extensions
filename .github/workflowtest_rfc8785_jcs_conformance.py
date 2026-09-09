# This is a basic workflow that is manually triggered

name: Manual workflow

# Controls when the action will run. Workflow runs when manually triggered using the UI
# or API.
on:
  workflow_dispatch:
    # Inputs the workflow accepts.
    inputs:
      name:
        # Friendly description to be shown in the UI instead of 'name'
        description: 'Person to greet'
        # Default value if no value is explicitly provided
        default: 'World'
        # Input has to be provided for the workflow to run
        required: true
        # The data type of the input
        type: string

# A workflow run is made up of one or more jobs that can run sequentially or in parallel
jobs:
  # This workflow contains a single job called "greet"
  greet:
    # The type of runner that the job will run on
    runs-on: ubuntu-latest

    # Steps represent a sequence of tasks that will be executed as part of the job
    steps:
    # Runs a single command using the runners shell
    - name: Send greeting
      run: echo "Hello ${{ inputs.name }}"
Sim. O vínculo que você estabeleceu está correto. Para esse repositório, eu faria a análise em camadas, sem tentar promover a existência dos workflows para execução.

O repositório json-schema-org/json-schema-spec é de fato o repositório público da especificação JSON Schema e contém .github, vitest-schema.config.js, package.json, os documentos da especificação etc. O próprio README informa que os testes do meta-schema podem ser executados com npm test e que existe configuração específica para Vitest. 

O que fazer agora 

Eu montaria o Evidence Graph deste repositório assim:

SCREENSHOT │ ▼ REPOSITORY_UI_OBSERVED │ ▼ REPOSITORY_IDENTITY │ ├── json-schema-org/json-schema-spec │ ├── branch/ref observada │ └── commit/ref temporal, se disponível │ ▼ ARTIFACT_IDENTITY │ ├── .github/workflows/ci.yml ├── .github/workflows/minimum-open-time.yml └── vitest-schema.config.js │ ▼ CONFIGURATION_EVIDENCE │ ├── workflow definition ├── triggers ├── jobs ├── runners ├── steps ├── commands └── test configuration │ └──────────────X──────────────► EXECUTION_EVIDENCE Depois, procurar a fronteira crítica 

O próximo passo não é concluir que os testes foram executados.

É procurar evidência concreta de:

WORKFLOW_RUN_OBSERVED │ ├── run_id ├── workflow_id ├── commit_sha ├── run_attempt ├── created_at ├── started_at ├── completed_at └── conclusion │ ▼ JOB_EXECUTION_OBSERVED │ ▼ STEP_EXECUTION_OBSERVED │ ▼ TEST_COMMAND_EXECUTED │ ▼ TEST_RESULT_OBSERVED │ ▼ INDEPENDENT_VERIFICATION │ ▼ VERIFIED_CLAIM 

Se esses elementos não forem encontrados, a conclusão correta permanece:

DECLARATIVE_CI_POLICY + TEST_CONFIGURATION + REPOSITORY_IDENTITY ↓ CONFIGURATION_EVIDENCE ↓ NOT_VERIFIED ↓ REQUIRED_EXECUTION_EVIDENCE_NOT_OBSERVED Há uma pista importante no próprio repositório 

O README declara que npm test executa os testes do meta-schema e que há um comando de cobertura. Isso é documentação operacional do projeto, não prova de que npm test foi executado em determinado momento. 

Da mesma forma, PROCESS.md descreve o processo de desenvolvimento/publicação da especificação e seus estágios de ciclo de vida; isso é evidência normativa/documental, não evidência de que um determinado processo ocorreu em uma execução específica. 

Portanto:

README └── npm test ↓ TEST_COMMAND_DOCUMENTED ↛ TEST_COMMAND_EXECUTED 

e:

PROCESS.md ↓ DEVELOPMENT_PROCESS_DOCUMENTED ↛ PROCESS_EVENT_EXECUTED ↛ PROCESS_EVENT_VERIFIED Eu criaria estes claims 

Para esse caso, a taxonomia ficaria especialmente limpa:

Claim Evidência atual REPOSITORY_IDENTITY SUPORTADO WORKFLOW_ARTIFACT_PRESENT SUPORTADO CI_CONFIGURATION_PRESENT SUPORTADO TEST_CONFIGURATION_PRESENT SUPORTADO TEST_COMMAND_DOCUMENTED SUPORTADO WORKFLOW_RUN_OBSERVED não demonstrado JOB_EXECUTION_OBSERVED não demonstrado TEST_EXECUTION_OBSERVED não demonstrado TEST_RESULT_OBSERVED não demonstrado TEST_ACCEPTANCE não demonstrado VERIFIED não promovível 

E eu acrescentaria uma distinção importante:

WORKFLOW CONFIGURATION ≠ PROJECT TEST CONFIGURATION ≠ TEST EXECUTION ≠ TEST RESULT ≠ TEST ACCEPTANCE 

Isso é particularmente importante porque o repositório realmente contém especificações e artefatos de validação. Por exemplo, o próprio repositório contém schemas relacionados ao output de validação e a especificação descreve resultados de validação. Isso demonstra o que o projeto especifica, não que uma execução concreta produziu aquele resultado. 

O próximo alvo de investigação 

Eu seguiria exatamente nesta ordem:

1. REPOSITORY_IDENTITY ↓ 2. COMMIT_IDENTITY ↓ 3. WORKFLOW_ARTIFACT_IDENTITY ↓ 4. WORKFLOW_CONFIGURATION ↓ 5. GITHUB_ACTIONS_RUN_OBSERVABILITY ↓ 6. RUN_ID ↓ 7. JOB/STEP EXECUTION ↓ 8. TEST COMMAND ↓ 9. TEST RESULT ↓ 10. ARTIFACT/COMMIT BINDING ↓ 11. INDEPENDENT VERIFICATION ↓ 12. CLAIM DECISION 

O ponto decisivo agora é o passo 5/6: descobrir se existe um workflow_run concreto e identificável.

Se houver run_id, aí podemos abrir uma segunda camada forense e verificar run → job → step → comando → resultado → commit, sem jamais inferir execução apenas a partir dos arquivos YAML.

