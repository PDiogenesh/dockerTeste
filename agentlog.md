# Agent Log - Contexto do Projeto

Atualizado em: 2026-04-30

## Visao geral

Este projeto e um ambiente Docker para estudar alta disponibilidade e balanceamento de carga com WordPress, MySQL, Nginx e Locust.

O objetivo principal ate agora foi montar uma arquitetura com varias instancias WordPress atras de um Nginx usando balanceamento Round Robin, depois executar testes de carga variando quantidade de usuarios e quantidade de instancias da aplicacao.

## Arquitetura atual

Servicos definidos em `docker-compose.yaml`:

- `mysql-db`: banco MySQL 5.7, com dados persistidos em `mysql_data/`.
- `wordpress1`: WordPress 5.4.2 com PHP 7.2 e Apache.
- `wordpress2`: segunda instancia WordPress igual a primeira.
- `wordpress3`: terceira instancia WordPress igual a primeira.
- `nginx`: balanceador de carga exposto na porta `80`.
- `locust`: gerador de carga exposto na porta `8089`.

Rede Docker:

- `wordpress-net`: rede bridge compartilhada pelos containers.

Volumes principais:

- `./html:/var/www/html` nas instancias WordPress.
- `./mysql_data:/var/lib/mysql` no MySQL.
- `./locust:/mnt/locust` no Locust.
- `./reports:/mnt/locust/reports` para salvar CSVs dos testes.

## Balanceamento Nginx

Existem tres arquivos de configuracao para alternar a quantidade de instancias WordPress durante os testes:

- `nginx-1.conf`: usa apenas `wordpress1`.
- `nginx-2.conf`: usa `wordpress1` e `wordpress2`.
- `nginx.conf`: usa `wordpress1`, `wordpress2` e `wordpress3`.

O Nginx usa upstream chamado `wordpress` e faz `proxy_pass http://wordpress`. Como nao ha estrategia especial configurada, o comportamento e Round Robin padrao do Nginx.

O `docker-compose.yaml` usa a variavel `NGINX_CONF`:

```powershell
${NGINX_CONF:-./nginx.conf}:/etc/nginx/nginx.conf:ro
```

Assim, o script de testes consegue recriar o Nginx apontando para 1, 2 ou 3 instancias.

## WordPress e banco

O WordPress esta persistido em `html/`, incluindo `wp-config.php`, `wp-content/`, `wp-admin/` e `wp-includes/`.

As credenciais usadas no Compose sao:

- Banco: `wordpress`
- Usuario: `usr-wordpress`
- Senha: `pwd-wordpress`
- Root password MySQL: `r00t`
- Host do banco para WordPress: `mysql-db`

Essas credenciais estao no projeto para ambiente local e academico.

## Locust

Arquivo principal:

- `locust/locustfile.py`

O comportamento do usuario virtual e simples:

- Le a variavel `TARGET_PATHS`.
- Separa multiplos caminhos por virgula.
- Para cada caminho, faz `GET`.
- Usa `wait_time` configuravel por `WAIT_TIME_MIN` e `WAIT_TIME_MAX`, com padrao de 1 a 3 segundos.

Classe principal:

- `WordpressUser(HttpUser)`

Task principal:

- `view_posts`

## Cenarios de teste

Os testes do Trabalho 3 usam tres posts:

- `/?p=5`: post com imagem de aproximadamente 1 MB.
- `/?p=10`: post com texto de aproximadamente 400 KB.
- `/?p=13`: post com imagem de aproximadamente 300 KB.

Variacoes executadas:

- Usuarios simultaneos: `10`, `100`, `1000`.
- Instancias WordPress: `1`, `2`, `3`.
- Duracao documentada no README: `30s` por teste.

Total planejado:

```text
3 cenarios x 3 quantidades de usuarios x 3 quantidades de instancias = 27 testes
```

## Automacao dos testes

Script principal:

- `scripts/run-load-tests.ps1`

O script:

1. Define os cenarios de teste.
2. Sobe `mysql-db`, `wordpress1`, `wordpress2`, `wordpress3` e `locust`.
3. Para cada quantidade de instancias, define `NGINX_CONF`.
4. Recria o container `nginx`.
5. Executa o Locust em modo headless.
6. Salva CSVs em `reports/`.
7. Ao final, roda `python scripts/generate-graphs.py`.

Comando para rodar todos os testes:

```powershell
.\scripts\run-load-tests.ps1 -Duration "30s"
```

Tambem existe um smoke test ja gerado em `reports/smoke_test_*`.

## Relatorios gerados

Pasta principal:

- `reports/`

Arquivos importantes:

- `reports/summary.csv`: consolidado das metricas agregadas.
- `reports/*_stats.csv`: metricas finais de cada execucao.
- `reports/*_stats_history.csv`: historico durante cada teste.
- `reports/*_failures.csv`: falhas por teste.
- `reports/*_exceptions.csv`: excecoes por teste.
- `reports/graphs/`: graficos de linha em SVG.
- `reports/bar_graphs/`: graficos de barras em SVG.

Contagem atual observada:

- CSVs em `reports/`: 117.
- SVGs em `reports/graphs/`: 40.
- SVGs em `reports/bar_graphs/`: 30.

Observacao: os 30 SVGs em `bar_graphs` correspondem aos 3 cenarios principais x 5 metricas x 2 formas de agrupamento.

## Geracao de graficos

Scripts:

- `scripts/generate-graphs.py`
- `scripts/generate-bar-graphs.py`

`generate-graphs.py`:

- Le `reports/*_stats.csv`.
- Procura a linha `Aggregated`.
- Gera ou atualiza `reports/summary.csv`.
- Gera graficos de linha em `reports/graphs/`.

`generate-bar-graphs.py`:

- Le `reports/summary.csv`.
- Gera graficos de barras em `reports/bar_graphs/`.
- Converte tempos de ms para segundos nos graficos finais.

Comando para regenerar graficos de barras:

```powershell
python scripts/generate-bar-graphs.py
```

## Resultados principais

Metricas analisadas:

- Tempo medio de resposta.
- Requisicoes por segundo.
- Quantidade de falhas.
- Percentil 95.
- Percentil 99.

Leitura geral dos resultados:

- Com `10` e `100` usuarios, os testes principais ficaram sem falhas.
- Com `1000` usuarios, apareceram falhas em 9 combinacoes, ou seja, nos 3 cenarios principais para 1, 2 e 3 instancias.
- As falhas em carga alta incluem HTTP 500, conexao resetada e conexao encerrada sem resposta.
- Aumentar instancias melhorou throughput em varios casos de 1000 usuarios, mas nao eliminou falhas.
- O gargalo ainda aparece sob carga alta, provavelmente envolvendo limite de processamento do WordPress/PHP/Apache, banco MySQL, conexoes ou recursos do ambiente Docker local.

Piores tempos medios observados em `summary.csv`:

- `post_400kb`, 1 WP, 1000 usuarios: media de aproximadamente `1767.65 ms`, 1253 falhas, p99 de `5600 ms`.
- `post_400kb`, 3 WP, 1000 usuarios: media de aproximadamente `1526.44 ms`, 2398 falhas, p99 de `4800 ms`.
- `imagem_1mb`, 1 WP, 1000 usuarios: media de aproximadamente `1483.37 ms`, 1407 falhas, p99 de `4100 ms`.

Maiores taxas de requisicoes por segundo observadas:

- `imagem_1mb`, 2 WP, 1000 usuarios: aproximadamente `262.44 req/s`, com 3522 falhas.
- `imagem_300kb`, 3 WP, 1000 usuarios: aproximadamente `260.37 req/s`, com 2704 falhas.
- `imagem_1mb`, 3 WP, 1000 usuarios: aproximadamente `259.04 req/s`, com 3127 falhas.

Exemplo de teste sem excecoes:

- `reports/imagem_1mb_1wp_10users_exceptions.csv` contem apenas o cabecalho, indicando ausencia de excecoes registradas nesse teste.

Exemplo de falhas em carga alta:

- `reports/post_400kb_2wp_1000users_failures.csv` registra HTTP 500, conexoes resetadas e conexoes encerradas sem resposta.

## README

O `README.md` ja foi organizado com:

- Descricao da arquitetura.
- Pre-requisitos.
- Como executar com Docker Compose.
- Como executar manualmente.
- Secao do Trabalho 3.
- Cenarios de carga.
- Arquivos importantes.
- Como rodar todos os testes.
- Como gerar graficos.
- Exemplos de graficos finais.
- Observacao sobre falhas com 1000 usuarios.

Ultimos commits relevantes:

- `371f249` - Organize README with Locust results
- `fcd4a9f` - Add Locust load testing reports
- `ad1e495` - mudei o readme

## Estado Git antes deste log

Antes da criacao deste arquivo, `git status --short` nao mostrou alteracoes pendentes.

Depois deste arquivo, a alteracao esperada e:

- Novo arquivo `agentlog.md`.

## Comandos uteis

Subir o ambiente:

```powershell
docker-compose up -d
```

Ver containers:

```powershell
docker ps
```

Ver logs do Nginx:

```powershell
docker logs --tail 60 nginx
```

Rodar smoke test manual pelo Locust:

```powershell
docker-compose exec -e TARGET_PATHS="/?p=1" locust locust -f locustfile.py --host http://nginx --headless -u 1 -r 1 -t 5s --csv reports/smoke_test
```

Rodar bateria completa:

```powershell
.\scripts\run-load-tests.ps1 -Duration "30s"
```

Regenerar graficos de linha e resumo:

```powershell
python scripts/generate-graphs.py
```

Regenerar graficos de barras:

```powershell
python scripts/generate-bar-graphs.py
```

## Pontos de atencao

- `mysql_data/` e uma pasta de dados locais e pode ficar grande.
- `html/` contem uma instalacao WordPress inteira versionada/local no workspace.
- Os testes de 1000 usuarios geram falhas e isso deve ser tratado como resultado experimental, nao necessariamente erro do script.
- O ambiente usa imagens antigas por requisito/contexto do trabalho: MySQL 5.7, WordPress 5.4.2 PHP 7.2, Nginx 1.19.0.
- O arquivo `nginx.conf` atual representa o cenario com 3 instancias.
- Para testar 1 ou 2 instancias, usar `NGINX_CONF` ou o script de testes.

## Proximos passos possiveis

- Escrever a analise final comparando 1, 2 e 3 instancias.
- Incluir interpretacao dos graficos no README ou em um relatorio separado.
- Explicar por que aparecem falhas HTTP 500 em 1000 usuarios.
- Conferir limites de Apache/PHP/MySQL se o objetivo for reduzir falhas.
- Ignorar ou documentar melhor `mysql_data/` caso o repositorio seja entregue sem dados locais.
