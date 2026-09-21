# Monitor de Atividade para Cato Networks Sites

Automação em Python para o monitoramento de status de links e sites (Sockets LAN/WAN) gerenciados pela Cato Networks.
Os alertas detectados são personalizados e enviados via Microsoft Teams e WhatsApp.

## Funcionalidades
- **Detecção de Quedas e Retornos:** Identifica transições de status ('Online ➔ Offline' e 'Offline ➔ Online').
- **Regra de Tolerância:** Aguarda 3 minutos antes do disparo de alertas, evitando a notificação de falsos positivos.
- **Inteligência de Isolamento:** Diferencia a queda isolada de um link ('LINK OFFLINE') da queda total de um site ('SITE OFFLINE').
- **Lembrete Diário:** Varredura automática diária que notifica a equipe sobre links que permanecem inativos e o tempo de indisponibilidade.

## Tecnologias Utilizadas
- **Python** - Lógica principal e orquestração.
- **Cato GraphQL API** - Consulta de telemetria e topologia.
- **Microsoft Teams Webhook** - Alertas corporativos para o Microsoft Teams.
- **WhatsApp Cloud API (Meta)** - Alertas corporativos para o WhatsApp.
- **Docker** - Conteinerização e isolamento do ambiente.

## Pré-requisitos
O projeto não disponibiliza o arquivo `.env` (credenciais). Será necessária a criação do mesmo por quem clonar o projeto.