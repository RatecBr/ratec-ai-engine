# RATEC AI ENGINE — Deploy Checklist

Utilize esta lista de verificação sempre que uma nova versão do RATEC AI ENGINE for promovida para o ambiente de produção.
Este processo assume que a automação de CI/CD (GitHub Actions) já concluiu o build das imagens Docker.

## 1. Preparação (Pre-Deploy)
- [ ] Confirme no painel do **GitHub Actions** que o workflow `build-serverless.yml` foi acionado (ele não rodará se não houverem mudanças no backend).
- [ ] Verifique se o workflow foi finalizado com status de **Sucesso**.
- [ ] Obtenha o **Short Hash** da versão no log do Actions (ex: `serverless-1ec6fa9` - observe que são os 7 primeiros caracteres do commit, e não o hash inteiro).
- [ ] Confirme se o Web Console (`engine.ra.tec.br`) correspondente já teve sua build finalizada com sucesso pela Vercel.

## 2. Atualização de Infraestrutura (Opcional se alterada via CLI, Obrigatório no RunPod)
- [ ] Acesse o Painel Web do RunPod (aba Serverless).
- [ ] Atualize o campo **Container Image** colando explicitamente a tag imutável do commit.
- [ ] **IMPORTANTE:** Nunca utilize a tag `:latest` ou `:serverless` diretamente em produção, caso contrário o cache local do RunPod pode não puxar a nova imagem.
- [ ] Salve as configurações do Endpoint.

## 3. Validação Operacional (Observabilidade)
A plataforma RATEC AI ENGINE expõe dados de observabilidade robustos no próprio Console. 

- [ ] Acesse o **Command Center** do Web Console.
- [ ] Localize o card **Engine Information**.
- [ ] **Commit Check:** O hash do commit exibido na UI bate perfeitamente com a tag que você acabou de colocar no RunPod?
- [ ] **Boot Check:** A data do *Worker Boot* exibe "agora" (o timestamp bate com os últimos minutos)?
- [ ] **Image Check:** O nome da imagem Docker reflete a tag exata inserida no painel?

Se todas as respostas acima forem **SIM**, o deploy de infraestrutura foi injetado com sucesso.

## 4. Testes de Integração (Health e Rotas Vitais)
Após a telemetria confirmar a versão rodando, efetue validações das camadas de serviço:
- [ ] O **Dashboard** apresenta `SYSTEM HEALTHY` ou status `ok`?
- [ ] O card de **GPU** detecta a Placa e o consumo de VRAM corretamente?
- [ ] Consiga acessar a aba **Models** e observe se as listagens de IA funcionam via Gateway.
- [ ] Execute uma previsão em um workflow "Hello World" de teste, validando o processamento assíncrono.

## 5. Manutenção Pós-Deploy e Rollback
- [ ] Caso a fase 4 falhe criticamente, execute o **Rollback Imediato**:
  - Re-edite o Endpoint no RunPod alterando o `Container Image` para o commit da versão anterior estável.
  - Revise e repita os passos da Seção 3.
- [ ] Se aprovado, marque o release no Github (tag) referenciando este commit.
