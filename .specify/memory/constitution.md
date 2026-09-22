<!--
### Sync Impact Report
- Version change: Unversioned Template (0.0.0) → 1.0.0
- Ratification Date: 2026-09-21
- Last Amended Date: 2026-09-21
- Modified principles:
  - PRINCIPLE_1_NAME → I. Resiliência de Estado (NON-NEGOTIABLE)
  - PRINCIPLE_2_NAME → II. Operações de Rede Defensivas
  - PRINCIPLE_3_NAME → III. Isolamento Estrito de Segredos
  - PRINCIPLE_4_NAME → IV. Configuração Fail-Fast
  - PRINCIPLE_5_NAME → V. Carga Cognitiva e Fadiga de Alerta
- Added sections:
  - Diretrizes Técnicas e Operacionais (SECTION_2)
  - Fluxo de Desenvolvimento e Garantia de Qualidade (SECTION_3)
- Removed sections: None
- Follow-up TODOs: None (all placeholders resolved)
-->

# Monitoramento Cato Networks Constitution

## Core Principles

### I. Resiliência de Estado (NON-NEGOTIABLE)
Contêineres são efêmeros e processos em background reiniciam. Depender exclusivamente da memória RAM para controlar a janela de tolerância de 3 minutos gera alertas falsos ou duplicados.
- Toda transição de estado (Queda ou Retorno) e seu respectivo `timestamp` DEVEM ser persistidos em disco rígido/volume montado ANTES de qualquer ação externa (ex.: despacho de notificações).
- O arquivo de estado JSON DEVE ser gravado de forma estritamente atômica: escrita inicial em arquivo temporário (`.tmp`) seguida de substituição atômica via operação nativa do sistema operacional (ex.: `os.replace`), prevenindo corrupção se o contêiner for encerrado ou sofrer crash durante a escrita.

### II. Operações de Rede Defensivas
As APIs de terceiros (Cato Networks GraphQL, Meta Cloud API, Teams Webhook) estão sujeitas a variações de latência, erros transitórios 5xx, rate-limiting e instabilidades de conectividade.
- Nenhuma requisição de rede PODE ser bloqueante por tempo indefinido ou capaz de abortar o loop principal de execução (Daemon).
- Toda requisição HTTP (GET, POST) DEVE definir timeout explícito e rigoroso (recomenda-se entre 10 e 15 segundos).
- Exceções de conexão (`ConnectionError`, `Timeout`, erros de socket e protocolo) DEVEM ser capturadas localmente no escopo de cada função cliente, registradas em log seguro e suprimidas, garantindo que o ciclo seguinte de monitoramento execute sem interrupção.

### III. Isolamento Estrito de Segredos
Tokens e chaves de API (Cato API Key, Meta Token, Webhooks) concedem acesso a telemetria sensível e canais corporativos amplos; vazamentos configuram risco de segurança crítico.
- O código-fonte DEVE ser completamente cego quanto à origem das credenciais: nenhum dado sensível, credencial ou segredo pode estar hardcoded, persistido em logs ou commitado no controle de versão.
- Todos os segredos DEVEM ser consumidos exclusivamente a partir de variáveis de ambiente do sistema operacional ou orquestrador.
- Qualquer exibição ou saída de configuração em console ou log (inclusive modo debug) DEVE ser ofuscada (ex.: mascaramento no formato `****-****-1A2B`).

### IV. Configuração Fail-Fast
Uma automação que inicia sem credenciais válidas ou sem rotas de notificação funcionais falhará silenciosamente no momento da crise, gerando uma falsa sensação de monitoramento operacional.
- A ausência ou inconsistência de qualquer dependência ou variável de ambiente necessária DEVE impedir a inicialização imediatamente.
- O módulo de inicialização DEVE validar a presença e o formato das chaves (API Keys, URLs de Webhooks, IDs de conta) no momento da carga da aplicação.
- Se qualquer dependência ou variável obrigatória estiver ausente ou inválida, o processo DEVE encerrar imediatamente com código de saída não-zero (`exit 1`) antes de entrar no loop contínuo de monitoramento.

### V. Carga Cognitiva e Fadiga de Alerta
Alertar sobre oscilações transitórias de milissegundos sobrecarrega e desensibiliza a equipe de TI, levando ao hábito prejudicial de ignorar notificações críticas.
- As regras de notificação DEVEM priorizar o diagnóstico do raio de impacto real em vez de reportar status bruto ou instabilidades momentâneas.
- O fenômeno de "flapping" (oscilações rápidas de conectividade) DEVE ser absorvido e filtrado integralmente pela lógica da automação.
- Módulos de notificação externa SÓ PODEM ser acionados quando a condição temporal estrita de tolerância (Tolerância ≥ 3 minutos) for atingida no estado persistido em disco.
- As notificações DEVEM discriminar com clareza e precisão a degradação parcial (`LINK OFFLINE`) da degradação total de localidade (`SITE OFFLINE`).

## Diretrizes Técnicas e Operacionais
O ecossistema do daemon opera com foco em alta disponibilidade, previsibilidade e desacoplamento:
- **Ambiente de Execução**: Contêiner Docker executando processo Python contínuo, com ponto de montagem persistente para o arquivo de estado JSON e restrição de privilégios.
- **Topologia de Integrações**:
  - *Cato Networks GraphQL API*: Consulta de telemetria de Sockets LAN/WAN e topologia de conectividade.
  - *Meta Cloud API (WhatsApp)*: Canal de alerta crítico para acionamento direto via mensageria móvel.
  - *Microsoft Teams Webhook*: Canal colaborativo de registro e notificação para as salas de operação da equipe de TI.
- **Estratégia de Log e Telemetria**: Logs estruturados registrando ciclo de varredura, transições de estado identificadas e status de despacho das notificações, assegurando sanitização prévia contra vazamento de segredos.

## Fluxo de Desenvolvimento e Garantia de Qualidade
Todo desenvolvimento futuro, melhoria ou refatoração no projeto deve aderir aos seguintes portões de qualidade:
- **Validação de Conformidade**: Todo plano (`plan.md`), especificação (`spec.md`) e lista de tarefas (`tasks.md`) DEVE referenciar explicitamente a aderência aos cinco princípios inegociáveis.
- **Testes Obrigatórios**:
  - Teste de atomicidade de escrita e recuperação de arquivos de estado em cenários simulados de interrupção abrupta.
  - Testes unitários com mock de chamadas HTTP validando comportamento defensivo em timeouts, status 429 e status 5xx.
  - Teste de validação fail-fast assegurando saída com código não-zero na falta de variáveis de ambiente mandatórias.
- **Critérios de Aceite para Pull Requests**: Nenhuma alteração de código será aprovada caso viole o mascaramento de logs, remova timeouts de rede ou reintroduza dependência de estado volátil em RAM.

## Governance
A presente constituição estabelece os princípios soberanos do projeto "Monitoramento Cato Networks" e prevalece sobre qualquer outra prática, documento ou decisão pontual de implementação. Qualquer proposta, especificação técnica, plano de tarefas ou trecho de código que viole estes princípios deve ser sumariamente rejeitado ou retificado.

- **Procedimento de Emenda**: Emendas a esta constituição exigem proposta fundamentada, documentação explícita da motivação técnica ou operacional, avaliação de impacto de segurança e aprovação formal.
- **Versionamento Semântico da Constituição**:
  - *MAJOR (ex.: 2.0.0)*: Alterações estruturais que redefinam, abram exceções ou removam qualquer princípio inegociável ou regra de governança.
  - *MINOR (ex.: 1.1.0)*: Inclusão de novas diretrizes operacionais, ampliação substancial de seções de garantia de qualidade ou introdução de novos canais de mensageria.
  - *PATCH (ex.: 1.0.1)*: Ajustes redacionais, correções ortográficas ou refinamentos não-normativos que não alterem o escopo mandatório.
- **Auditoria Contínua**: Desenvolvedores e agentes de inteligência artificial DEVEM verificar e atestar a conformidade do projeto com este documento a cada iteração de ciclo de vida (planejamento, codificação e revisão).

**Version**: 1.0.0 | **Ratified**: 2026-09-21 | **Last Amended**: 2026-09-21
