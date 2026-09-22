# Feature Specification: Monitoramento de Sockets Cato Networks

**Feature Branch**: `001-cato-socket-monitoring`

**Created**: 2026-09-22

**Status**: Draft

**Input**: User description: "Especificação: Monitoramento de Sockets Cato Networks - Monitoramento proativo de status de links Cato Networks com filtro anti-flap de 3 minutos, alerta de LINK OFFLINE vs SITE OFFLINE, notificação de RETORNO e boletim diário às 08:00 via Teams e WhatsApp."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detecção e Alerta de Queda com Tolerância Anti-Flap (Priority: P1)

Como operador de redes da equipe de TI, desejo que o sistema monitore continuamente a conectividade de cada link e só dispare um alerta caso o link permaneça indisponível por 3 minutos ininterruptos, para que a equipe seja informada sobre incidentes reais sem sofrer com falso-positivos gerados por oscilações transitórias (flapping).

**Why this priority**: É a funcionalidade central de valor do monitoramento; sem a detecção periódica e o filtro de tolerância de 3 minutos, ou não há monitoramento ou a equipe sofrerá com fadiga de alertas por instabilidades momentâneas.

**Independent Test**: Pode ser testado simulando um link offline por menos de 3 minutos (ex.: 2 minutos) e validando que nenhum alerta é emitido; em seguida, simulando a inatividade por 3 minutos contínuos e confirmando o disparo imediato do alerta para Microsoft Teams e WhatsApp.

**Acceptance Scenarios**:

1. **Given** que todos os links de um site estão operacionais (status online), **When** um link transiciona para inativo (minuto 0), **Then** o sistema registra internamente o horário de queda, mantém silêncio e não despacha nenhuma notificação externa.
2. **Given** que um link caiu há 1 ou 2 minutos, **When** o ciclo de verificação subsequente constatar que o link continua inativo, **Then** o sistema mantém o silêncio de alerta até que o limiar de 3 minutos seja alcançado.
3. **Given** que um link está inativo continuamente há 3 minutos, **When** o ciclo do 3º minuto for concluído, **Then** o sistema transiciona o estado do alerta para "Enviado" e despacha imediatamente uma notificação de queda para o canal do Microsoft Teams e para o WhatsApp corporativo.
4. **Given** que um link caiu no minuto 0, **When** ele restabelecer a conexão antes do 3º minuto (ex.: aos 2 minutos), **Then** o sistema descarta o registro de queda pendente sem emitir nenhum alerta de queda nem de restabelecimento.

---

### User Story 2 - Notificação Instantânea de Restabelecimento (Retorno) (Priority: P2)

Como operador de redes da equipe de TI, desejo receber uma notificação imediata no momento em que um link ou localidade previamente alertada voltar a operar normalmente, para saber instantaneamente que o incidente foi superado sem precisar consultar manualmente portais externos.

**Why this priority**: Fecha o ciclo de vida do incidente, informando à equipe e aos gestores que o serviço foi restabelecido e evitando retrabalho na abertura ou acompanhamento de chamados.

**Independent Test**: Pode ser testado colocando um link no estado de alerta já enviado ("LINK OFFLINE" ou "SITE OFFLINE") e, ao detectar sua volta ao status operacional no próximo ciclo de consulta, verificar o envio imediato da mensagem de retorno para Teams e WhatsApp e a limpeza do incidente no registro persistente.

**Acceptance Scenarios**:

1. **Given** que um alerta de queda já foi disparado para um link, **When** a conectividade desse link for restabelecida no ciclo de monitoramento, **Then** o sistema despacha imediatamente uma notificação de "RETORNO" via Microsoft Teams e WhatsApp informando o nome do site, o link recuperado e a normalização.
2. **Given** que um link caiu e voltou antes de completar 3 minutos contínuos (sem envio prévio de alerta), **When** a conectividade for restabelecida, **Then** o sistema NÃO deve disparar notificação de retorno, garantindo total silêncio sobre a oscilação.

---

### User Story 3 - Diferenciação Inteligente de Impacto: Link Offline vs. Site Offline (Priority: P3)

Como gestor ou analista de infraestrutura, desejo que os alertas indiquem com clareza se a queda se restringe a uma degradação parcial (LINK OFFLINE) ou se representa a perda total de conectividade da filial (SITE OFFLINE), para mensurar o raio de impacto e a gravidade operacional no momento da notificação.

**Why this priority**: Proporciona triagem imediata; um link secundário caído requer abertura de chamado com a operadora, enquanto um site totalmente inativo exige plano de contingência e escalonamento emergencial de prioridade máxima.

**Independent Test**: Pode ser testado em um site com múltiplos links: derrubar apenas um link por 3 minutos e validar que o alerta enviado é rotulado como "LINK OFFLINE"; em seguida, derrubar simultaneamente todos os links daquele mesmo site e validar que o alerta é categorizado com severidade máxima como "SITE OFFLINE".

**Acceptance Scenarios**:

1. **Given** uma filial (site) com múltiplos links configurados onde apenas um deles atinge 3 minutos de inatividade, **When** o alerta for despachado, **Then** o título e corpo da notificação no Teams e no WhatsApp devem classificar o incidente como "LINK OFFLINE", especificando o nome da interface/operadora e informando que o site permanece acessível através dos demais links.
2. **Given** uma filial (site) onde todos os seus links atinjam a condição de inatividade, **When** o alerta for despachado, **Then** o título e corpo da notificação devem destacar visualmente "SITE OFFLINE", evidenciando que a filial está completamente isolada.
3. **Given** que um site estava em condição "SITE OFFLINE" e um de seus links é restabelecido enquanto outro continua fora, **When** a detecção ocorrer, **Then** o sistema notifica o retorno parcial da conectividade da filial e ajusta a classificação do incidente residual para "LINK OFFLINE".

---

### User Story 4 - Boletim Diário de Links Inativos para Gestão de Backlog (Priority: P4)

Como gestor de TI e redes, desejo receber diariamente às 08:00 um boletim consolidado informando quais links permanecem inativos e há quanto tempo (em dias e horas), para direcionar a equipe nas cobranças diárias às operadoras de telecomunicações e prestadores de serviço.

**Why this priority**: Permite acompanhamento contínuo de indisponibilidades prolongadas sem necessidade de spam ao longo do dia, transformando dados de inatividade em ações práticas no início do expediente.

**Independent Test**: Pode ser testado configurando incidentes com diferentes durações de inatividade (ex.: 2 horas, 3 dias) e disparando o envio do horário programado das 08:00, validando que uma mensagem consolidada é enviada exclusivamente ao canal do Microsoft Teams com a listagem ordenada e o cálculo exato do tempo de inatividade.

**Acceptance Scenarios**:

1. **Given** que existem um ou mais links inativos há mais de 3 minutos no momento das 08:00, **When** o horário configurado for atingido, **Then** o sistema envia uma mensagem consolidada exclusivamente para o Microsoft Teams com a relação de cada site, link inativo e tempo decorrido formatado em dias e horas.
2. **Given** que nenhum link está inativo às 08:00 (todos operacionais), **When** o horário do boletim for atingido, **Then** o sistema envia uma mensagem informando que 100% dos links e sites monitorados estão operacionais.
3. **Given** o disparo do boletim matinal das 08:00, **When** a mensagem for gerada, **Then** ela NÃO deve ser enviada para o canal de WhatsApp (evitando sobrecarga de mensagens em grupos de plantão), permanecendo restrita ao Microsoft Teams.

---

### User Story 5 - Resiliência Operacional e Preservação de Estado entre Reinicializações (Priority: P5)

Como administrador do sistema, desejo que a contagem de tempo de tolerância e o registro de incidentes já notificados sobrevivam a reinicializações da aplicação ou do contêiner, para que não ocorram alertas duplicados nem reinício indesejado da contagem de tolerância após uma manutenção.

**Why this priority**: Assegura a integridade e previsibilidade do sistema em ambiente conteinerizado sujeito a deploys e reinícios.

**Independent Test**: Pode ser testado colocando um link em inatividade há 2 minutos, reiniciando o processo e confirmando que, no minuto subsequente (totalizando 3 minutos), o alerta é disparado pontualmente; ou reiniciando o sistema com alertas já enviados e confirmando que nenhuma notificação repetida é emitida.

**Acceptance Scenarios**:

1. **Given** que um link está inativo há 2 minutos e a aplicação é reiniciada abruptamente, **When** o sistema retomar a execução e completar o próximo ciclo (minuto 3), **Then** o sistema reconhece o tempo acumulado anteriormente e despacha o alerta de queda sem reiniciar a contagem do zero.
2. **Given** que um alerta de queda já foi disparado para um link e a aplicação é reiniciada, **When** o sistema retomar e constatar que o link continua inativo, **Then** ele NÃO reenvia o alerta de queda, mantendo o estado de alerta ativo aguardando o restabelecimento (retorno) ou inclusão no boletim matinal.

---

### Edge Cases

- **Instabilidade ou falha temporária na consulta à API de telemetria**: Se a consulta de rede à Cato Networks falhar por timeout ou erro transitório, o ciclo atual não deve assumir que os links caíram; o sistema deve manter o estado anterior inalterado, registrar o erro em log sanitizado e tentar novamente no próximo ciclo sem interromper o serviço.
- **Falha temporária no canal de notificação (Teams ou WhatsApp)**: Se a tentativa de envio de alerta falhar por indisponibilidade momentânea do webhook ou da API Meta, o erro deve ser registrado de forma segura e o sistema deve manter o incidente registrado para tentativas subsequentes sem abortar a aplicação.
- **Flapping na fronteira exata dos 3 minutos**: Se um link oscilar entre online e offline (ex.: cai 2 minutos, volta 1 minuto, cai novamente), cada período de inatividade deve reiniciar o cômputo da janela ininterrupta de 3 minutos, evitando o envio prematuro de alertas.
- **Queda simultânea de todos os links de um site**: O sistema deve correlacionar os eventos e emitir prioritariamente o alerta de severidade total "SITE OFFLINE" em vez de múltiplos alertas desconexos de links individuais.
- **Recuperação parcial de um site**: Se um site com 2 links inativos tiver 1 link restabelecido, o sistema deve emitir o retorno da conectividade do site, alertando que a localidade agora opera de forma degradada com um "LINK OFFLINE" remanescente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE realizar polling periódico do status de todos os sockets e links da Cato Networks a cada 60 segundos.
- **FR-002**: O sistema DEVE identificar a relação entre cada link de rede e seu respectivo Site (filial), permitindo a detecção de integridade agregada do site.
- **FR-003**: O sistema DEVE registrar o timestamp exato do início da inatividade no momento em que um link for detectado como inativo pela primeira vez.
- **FR-004**: O sistema DEVE aplicar uma janela de tolerância de 3 minutos contínuos e ininterruptos de inatividade antes de qualificar um incidente como passível de notificação externa.
- **FR-005**: O sistema DEVE descartar silenciosamente qualquer registro de queda se o link retornar ao status operacional antes de completar os 3 minutos contínuos de tolerância.
- **FR-006**: Ao completar 3 minutos contínuos de inatividade, o sistema DEVE despachar imediatamente a notificação de queda através de webhook do Microsoft Teams e via Meta Cloud API (WhatsApp).
- **FR-007**: A notificação de queda DEVE explicitar o grau de severidade:
  - "LINK OFFLINE": quando o link caiu, mas ainda existe pelo menos um outro link operacional no mesmo site.
  - "SITE OFFLINE": quando todos os links vinculados àquele site estão inativos.
- **FR-008**: O sistema DEVE identificar quando um link ou site previamente alertado recuperar a conectividade e despachar imediatamente uma notificação de "RETORNO" para o Microsoft Teams e WhatsApp.
- **FR-009**: O sistema DEVE emitir diariamente às 08:00 (no fuso horário configurado) um boletim consolidado exclusivamente para o Microsoft Teams com a lista de links inativos e a respectiva duração calculada em dias e horas.
- **FR-010**: Caso nenhum link esteja inativo às 08:00, o sistema DEVE enviar um boletim matinal positivo confirmando que toda a infraestrutura monitorada está operacional.
- **FR-011**: O sistema DEVE persistir o estado de incidentes e monitoramento em disco não volátil de forma atômica a cada mudança de estado, assegurando sobrevivência a reinicializações.
- **FR-012**: O sistema DEVE carregar o estado salvo durante o processo de inicialização, preservando contagens de tempo e flags de notificações já despachadas.
- **FR-013**: O sistema DEVE validar na inicialização a existência e consistência de todas as configurações mandatórias (credenciais e parâmetros dos canais de alerta), encerrando a execução com código de erro caso haja inconsistência (Fail-Fast).
- **FR-014**: O sistema DEVE assegurar que nenhuma credencial (tokens, chaves de API, webhooks) seja impressa em texto plano nos logs ou em saídas de erro.

### Key Entities

- **Site (Filial)**: Entidade que representa uma localidade física conectada pela rede. Possui nome/identificador amigável e contém uma coleção de um ou mais Links.
- **Link (Conexão WAN/Socket)**: Entidade associada a um Site que representa uma interface física de telecomunicação/internet. Possui identificador único, nome de exibição, referência ao Site pai e estado atual de conectividade (Online ou Offline).
- **Incidente de Inatividade**: Entidade que controla o ciclo de vida da indisponibilidade de um Link. Contém a referência do Link, o timestamp da primeira detecção de queda, o tempo total acumulado em segundos, o status do alerta (Pendente_Tolerância ou Alerta_Enviado) e a classificação de impacto emitida (Link Offline ou Site Offline).
- **Boletim Diário**: Relatório sintético gerado no horário de corte matinal (08:00), consolidando todos os Incidentes de Inatividade ativos e ordenados por maior tempo de indisponibilidade.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das oscilações transitórias de conectividade com duração inferior a 3 minutos são absorvidas e descartadas sem disparo de alertas falsos nos canais externos.
- **SC-002**: Notificações de queda confirmada são despachadas aos canais (Teams e WhatsApp) em até 30 segundos após a conclusão da janela de tolerância de 3 minutos.
- **SC-003**: Notificações de restabelecimento (retorno) são despachadas aos canais em até 60 segundos após a detecção do retorno operacional do link.
- **SC-004**: 100% dos alertas diferenciam com exatidão a condição de perda total de conectividade da filial (SITE OFFLINE) da degradação parcial de links redundantes (LINK OFFLINE).
- **SC-005**: O boletim matinal das 08:00 é entregue pontualmente no Microsoft Teams em até 60 segundos após o horário estipulado, com o tempo acumulado de inatividade de cada link exibido com precisão de horas e dias.
- **SC-006**: Em caso de reinicialização ou interrupção do serviço, 100% do estado prévio é recuperado, sem perda do tempo acumulado de incidentes em andamento e sem reenvio indevido de alertas já despachados.

## Assumptions

- O monitor opera de forma ininterrupta (modo daemon / contêiner) com agendamento contínuo de 60 segundos para varredura de telemetria.
- A conta corporativa na Cato Networks fornece acesso a consultas de status de sockets e sites com latência aceitável (respostas esperadas em até 10-15 segundos).
- O fuso horário de referência para o envio do boletim diário das 08:00 é configurável no ambiente (padrão `America/Sao_Paulo`).
- O canal do Microsoft Teams (Webhook corporativo) e a conta WhatsApp Business (Meta Cloud API com template ou mensagem de texto aprovada) estão previamente provisionados com credenciais válidas.
- Os canais de notificação possuem suporte a formatação de mensagens (Markdown / Adaptive Cards no Teams e formatação de texto no WhatsApp).
- Existe um volume ou sistema de arquivos persistente montado no contêiner para que o arquivo de estado JSON sobreviva a reinicializações.
