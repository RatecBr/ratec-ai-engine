# RunPod Serverless Deployment Guide

Este documento descreve o procedimento operacional padrão para a atualização de Endpoints Serverless na plataforma RunPod.

Devido às políticas de segurança e permissões do RunPod, chaves de API restritas (Endpoint Keys) não possuem privilégios de alteração da infraestrutura em nuvem. Portanto, a atualização da imagem do container em execução é uma **etapa manual** exigida do administrador da conta.

## Pré-requisitos

1. Ter publicado com sucesso uma nova imagem através do pipeline de CI/CD (GitHub Actions).
2. A imagem deve utilizar a tag gerada automaticamente baseada no commit (ex: `serverless-1ec6fa9`), garantindo a imutabilidade do artefato em produção.
3. Possuir acesso administrativo logado no painel Web do RunPod.

---

## 🚀 Passo a Passo de Atualização

### Passo 1: Localizar a Nova Tag Imutável
- Abra o painel do **GitHub Actions**.
- Acesse a execução mais recente da branch de produção.
- Nos logs do step `Extract metadata` (ou no card de informações no painel do Web Console), copie a Tag gerada pelo commit mais recente.
  > Exemplo: `ghcr.io/ratecbr/ratec-ai-engine:serverless-1ec6fa9`

### Passo 2: Atualizar o Endpoint no RunPod
1. Acesse o [RunPod Web Console](https://www.runpod.io/console/serverless).
2. Acesse a aba **Serverless** > **Endpoints**.
3. Selecione o endpoint correspondente ao RATEC AI ENGINE.
4. Clique em **Settings** ou **Edit Endpoint**.
5. No campo **Container Image**, substitua a imagem antiga (ou a tag genérica `:serverless`) pela **Tag Imutável** identificada no Passo 1.
   - ⚠️ *Por que não usar a tag `:serverless` sempre?* 
     O RunPod faz cache agressivo de imagens. Utilizar tags imutáveis forçará o worker a descartar o cache local e efetuar o pull da versão correta.
6. Clique em **Save** para iniciar o processo de re-implantação.

### Passo 3: Reinício e Clean-up
- O RunPod automaticamente vai terminar os workers existentes (drenagem) e provisionar novos com a imagem atualizada.
- Acompanhe a aba **Workers** até que um worker com status "Ready" seja listado.
- Caso o Endpoint esteja vinculado a um Network Volume e houver conflito de dependências engessadas no volume, valide se o código antigo não está sendo sobreposto ao novo. Se necessário, purge o Network Volume de arquivos temporários e caches desatualizados.

---

## 🔍 Validação da Implantação

Após a atualização do Endpoint, a validação da versão em execução **deverá ser feita obrigatoriamente** utilizando as ferramentas nativas de observabilidade da plataforma.

### Pelo Web Console (Recomendado)
1. Acesse o **Command Center** do Web Console (`https://engine.ra.tec.br`).
2. Localize o card **"Engine Information"**.
3. Valide se as informações apresentadas correspondem à versão esperada:
   - **Commit**: Confirme se o hash bate com a versão do Git.
   - **Docker Image**: Confirme se bate com a tag que foi digitada no RunPod.
   - **Build Date**: Confirme se a data é recente.

### Pela API (Fallback)
Faça uma requisição ao endpoint de telemetria da versão:

```bash
curl -X GET "https://[ID_DO_SEU_ENDPOINT].api.runpod.net/admin/version" \
     -H "Authorization: Bearer [SUA_CHAVE_DE_API]"
```

A resposta retornará o `VersionProvider` com os metadados integrados (incluindo o timestamp exato do início do worker `worker_started_at`).

## Rollback

Caso a nova versão apresente regressões na fase de validação:
1. Retorne ao Painel Web do RunPod (Passo 2).
2. Altere o **Container Image** novamente, colando a **tag do commit anterior** (que encontrava-se estável).
3. Salve, reinicie e revalide utilizando o Command Center.
