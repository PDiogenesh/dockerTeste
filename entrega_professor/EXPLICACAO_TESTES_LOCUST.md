# Explicacao dos Testes de Carga com Locust

Este material resume como os testes foram feitos, desde a criacao/configuracao do Locust ate a geracao dos CSVs e graficos usados na apresentacao.

## 1. O que foi separado nesta pasta

Pasta `entrega_professor/`:

- `csvs_importantes/`: contem os 36 CSVs principais de estatisticas finais do Locust, um para cada combinacao testada, mais o `summary.csv` consolidado.
- `graficos_importantes/`: contem 40 graficos finais em SVG, gerados a partir do `summary.csv`.
- `EXPLICACAO_TESTES_LOCUST.md`: este roteiro de explicacao.

Os 36 CSVs principais seguem esta matriz:

```text
4 cenarios x 3 cargas de usuarios x 3 quantidades de instancias = 36 testes
```

## 2. Arquitetura usada

O ambiente foi montado com Docker Compose no arquivo `docker-compose.yaml`.

Servicos usados:

- `mysql-db`: banco MySQL 5.7 usado pelo WordPress.
- `wordpress1`, `wordpress2`, `wordpress3`: tres instancias iguais do WordPress.
- `nginx`: balanceador de carga, exposto na porta `80`.
- `locust`: gerador de carga, com a imagem `locustio/locust:2.24.1`.

O Nginx fica na frente das instancias WordPress. Os usuarios simulados pelo Locust acessam o Nginx, e o Nginx distribui as requisicoes para as instancias WordPress.

Foram usados tres arquivos de configuracao do Nginx:

- `nginx-1.conf`: usa apenas `wordpress1`.
- `nginx-2.conf`: usa `wordpress1` e `wordpress2`.
- `nginx.conf`: usa `wordpress1`, `wordpress2` e `wordpress3`.

Assim foi possivel comparar o desempenho com 1, 2 e 3 instancias.

## 3. Como o Locust foi criado

No `docker-compose.yaml`, foi adicionado o servico `locust`:

```yaml
locust:
  image: locustio/locust:2.24.1
  container_name: locust
  ports:
    - "8089:8089"
  volumes:
    - ./locust:/mnt/locust
    - ./reports:/mnt/locust/reports
  working_dir: /mnt/locust
  command: -f locustfile.py --host http://nginx
```

Pontos importantes:

- `./locust:/mnt/locust`: coloca o arquivo `locustfile.py` dentro do container.
- `./reports:/mnt/locust/reports`: salva os CSVs gerados pelo Locust na pasta local `reports/`.
- `--host http://nginx`: o alvo dos testes e o container `nginx`, nao uma instancia WordPress especifica.

## 4. Comportamento simulado no Locust

O comportamento dos usuarios virtuais esta em `locust/locustfile.py`.

Resumo do funcionamento:

- O Locust le a variavel de ambiente `TARGET_PATHS`.
- Essa variavel define qual post do WordPress sera acessado.
- Cada usuario virtual faz requisicoes HTTP `GET` para o post definido.
- O tempo de espera entre requisicoes fica entre 1 e 3 segundos.

Trecho principal:

```python
class WordpressUser(HttpUser):
    wait_time = between(
        float(os.getenv("WAIT_TIME_MIN", "1")),
        float(os.getenv("WAIT_TIME_MAX", "3")),
    )

    @task
    def view_posts(self):
        for path in _target_paths():
            self.client.get(path, name=path)
```

Ou seja: cada usuario simulado acessa um post do WordPress repetidamente durante o tempo do teste.

## 5. Cenarios testados

Foram testados 4 posts:

| Cenario | ID do post | Descricao |
|---|---:|---|
| `imagem_1mb` | `/?p=5` | Post com imagem de aproximadamente 1 MB |
| `post_400kb` | `/?p=10` | Post com texto de aproximadamente 400 KB |
| `imagem_300kb` | `/?p=13` | Post com imagem de aproximadamente 300 KB |
| `hibrido_1mb_texto_400kb` | `/?p=17` | Post hibrido com imagem de aproximadamente 1 MB e texto de aproximadamente 400 KB |

Para cada cenario, foram testadas:

- cargas de usuarios: `10`, `100`, `1000`;
- instancias WordPress: `1`, `2`, `3`;
- duracao por teste: `30s`.

## 6. Automacao dos testes

Os testes foram automatizados no script `scripts/run-load-tests.ps1`.

Comando para rodar a bateria completa:

```powershell
.\scripts\run-load-tests.ps1 -Duration "30s"
```

O script faz este fluxo:

1. Define os 4 cenarios de teste.
2. Sobe os containers `mysql-db`, `wordpress1`, `wordpress2`, `wordpress3` e `locust`.
3. Para cada quantidade de instancias, escolhe o arquivo Nginx correto.
4. Recria o container `nginx` com 1, 2 ou 3 instancias no balanceamento.
5. Executa o Locust em modo headless.
6. Salva os CSVs em `reports/`.
7. Gera o `summary.csv`.
8. Gera os graficos finais.

Exemplo do comando Locust executado pelo script:

```powershell
docker-compose exec -e TARGET_PATHS="/?p=5" locust locust `
  -f locustfile.py `
  --host http://nginx `
  --headless `
  -u 100 `
  -r 20 `
  -t "30s" `
  --csv reports/imagem_1mb_1wp_100users `
  --csv-full-history
```

Parametros principais:

- `-u`: numero de usuarios simultaneos.
- `-r`: taxa de criacao de usuarios por segundo.
- `-t`: duracao do teste.
- `--csv`: prefixo dos arquivos CSV gerados.
- `--csv-full-history`: salva historico do teste ao longo do tempo.

## 7. Como os CSVs foram gerados

Para cada execucao, o Locust gera arquivos como:

```text
imagem_1mb_1wp_10users_stats.csv
imagem_1mb_1wp_10users_failures.csv
imagem_1mb_1wp_10users_exceptions.csv
imagem_1mb_1wp_10users_stats_history.csv
```

O arquivo mais importante para comparacao final e o `*_stats.csv`, porque ele contem a linha `Aggregated`, que resume o resultado total da execucao.

Por isso, nesta pasta foram separados os 36 arquivos `*_stats.csv`, um para cada combinacao.

O arquivo `summary.csv` foi gerado lendo a linha `Aggregated` de cada `*_stats.csv`.

Metricas consolidadas:

- `Average Response Time`: tempo medio de resposta em milissegundos.
- `Requests/s`: requisicoes por segundo.
- `Failure Count`: quantidade de falhas.
- `95%`: percentil 95 do tempo de resposta.
- `99%`: percentil 99 do tempo de resposta.

## 8. Como os graficos foram gerados

Os graficos foram gerados por dois scripts:

- `scripts/generate-graphs.py`: gera graficos de linha em `reports/graphs/`.
- `scripts/generate-bar-graphs.py`: gera graficos de barras em `reports/bar_graphs/`.

Para a apresentacao, foram separados os graficos de barras, porque eles facilitam comparar:

- usuarios no eixo X e instancias como series;
- instancias no eixo X e usuarios como series.

Foram gerados 40 graficos:

```text
4 cenarios x 5 metricas x 2 formas de agrupamento = 40 graficos
```

As 5 metricas graficadas foram:

- tempo medio de resposta;
- requisicoes por segundo;
- quantidade de falhas;
- percentil 95;
- percentil 99.

## 9. Como explicar os resultados

Uma forma simples de apresentar:

1. Primeiro mostrar a arquitetura: Locust -> Nginx -> WordPress -> MySQL.
2. Explicar que o Nginx foi alterado para testar 1, 2 e 3 instancias.
3. Mostrar que cada post foi testado com 10, 100 e 1000 usuarios.
4. Abrir o `summary.csv` para mostrar que existem 36 linhas, uma por combinacao.
5. Mostrar os graficos de tempo medio e requisicoes por segundo.
6. Depois mostrar os graficos de falhas e percentis para discutir saturacao.

Leitura geral dos resultados:

- Com 10 e 100 usuarios, os testes tendem a ficar estaveis e sem falhas.
- Com 1000 usuarios, aparecem falhas HTTP 500 e conexoes encerradas/resetadas em alguns cenarios.
- Aumentar instancias geralmente melhora throughput em varios cenarios, mas nao elimina totalmente as falhas em carga alta.
- Isso indica que o gargalo pode estar no WordPress/PHP/Apache, no MySQL, no limite de conexoes ou nos recursos do ambiente Docker local.

Observacao importante:

No teste hibrido com 1000 usuarios, o Locust registrou aviso de CPU acima de 90%. Portanto, esses resultados devem ser lidos como indicio de saturacao do ambiente de teste.

## 10. Resposta curta caso o professor pergunte "como foi feito?"

Foi criado um container Locust no Docker Compose, apontando para o Nginx. O Nginx balanceia as requisicoes entre 1, 2 ou 3 containers WordPress. O arquivo `locustfile.py` simula usuarios acessando posts especificos do WordPress via GET. Um script PowerShell automatiza a troca da configuracao do Nginx, executa o Locust em modo headless para 10, 100 e 1000 usuarios, salva os CSVs e depois gera um resumo e graficos das metricas coletadas.
