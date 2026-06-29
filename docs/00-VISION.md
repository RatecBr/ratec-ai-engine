# RATEC AI ENGINE

## Visão

O RATEC AI ENGINE é a plataforma oficial de Inteligência Artificial da RATEC.

Este projeto não pertence ao GOODLOOK. Ele será utilizado por todos os produtos atuais e futuros da RATEC.

## Missão

Construir uma plataforma única, modular e escalável de IA, onde todos os aplicativos consumam apenas uma API.

## Princípios

- Desacoplamento total entre aplicativos e modelos de IA.
- Workflows independentes.
- Providers substituíveis.
- API versionada.
- Execução em RunPod Serverless (NVIDIA RTX A5000, scale-to-zero).
- ComfyUI como motor de execução de imagens (integrado e em produção).
- Modelos de IA nunca embutidos na imagem Docker — carregados via Network Volume.
- IaC: todo setup do ambiente é código, nunca configuração manual.

## Arquitetura

Aplicativo Cliente

↓

RATEC AI ENGINE

↓

Workflow Engine

↓

Providers

↓

Modelos de IA

↓

GPU

## Consumidores

- GOODLOOK
- Audiover
- Internice
- Animapages
- Karaokêro
- Tradulino
- Novos produtos da RATEC
