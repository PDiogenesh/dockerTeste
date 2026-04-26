# Projeto: Arquitetura de Alta Disponibilidade com WordPress e Nginx

Esse projeto implementa uma infraestrutura escalável com Docker, composta por um banco de dados MySQL centralizado, três instâncias da aplicação WordPress e um balanceador de carga Nginx para distribuir o tráfego entre os serviços.

## Trabalho 3 - Testes de Carga com Locust

Este projeto tambem inclui um container do Locust para gerar carga contra o Nginx, que e o balanceador de carga das instancias WordPress.

### Arquivos adicionados

- `locust/locustfile.py`: script de teste de carga.
- `reports/`: pasta onde os CSVs dos testes podem ser salvos.
- `nginx-1.conf`: Nginx usando somente `wordpress1`.
- `nginx-2.conf`: Nginx usando `wordpress1` e `wordpress2`.
- `nginx.conf`: Nginx usando as 3 instancias (`wordpress1`, `wordpress2`, `wordpress3`).

### Subir o ambiente com Locust

```bash
docker-compose up -d
```

Depois acesse:

```text
http://localhost:8089
```

Na tela do Locust, use:

```text
Host: http://nginx
```

### Configurar qual post sera testado

O script usa a variavel `TARGET_PATHS`. Exemplos:

```powershell
$env:TARGET_PATHS="/?p=1"
docker-compose up -d --force-recreate locust
```

```powershell
$env:TARGET_PATHS="/?p=2"
docker-compose up -d --force-recreate locust
```

```powershell
$env:TARGET_PATHS="/?p=3"
docker-compose up -d --force-recreate locust
```

Use o ID real de cada post criado no WordPress:

- Post com imagem de aproximadamente 1 MB: `/?p=5`.
- Post de aproximadamente 400 KB: `/?p=10`.
- Post com imagem de aproximadamente 300 KB: `/?p=13`.

### Rodar todos os testes e gerar graficos

O script abaixo executa os 27 testes do trabalho:

```text
3 posts x 3 quantidades de usuarios x 3 quantidades de instancias WordPress
```

```powershell
.\scripts\run-load-tests.ps1
```

Por padrao, cada teste dura 1 minuto. Para mudar a duracao:

```powershell
.\scripts\run-load-tests.ps1 -Duration "30s"
```

Ao final, os CSVs ficam em `reports/` e os graficos ficam em:

```text
reports/graphs
```

Se os CSVs ja existirem e voce quiser gerar os graficos novamente:

```powershell
python scripts/generate-graphs.py
```

### Variar o numero de instancias do WordPress

Para testar com 1 instancia:

```powershell
$env:NGINX_CONF="./nginx-1.conf"
docker-compose up -d --force-recreate nginx
```

Para testar com 2 instancias:

```powershell
$env:NGINX_CONF="./nginx-2.conf"
docker-compose up -d --force-recreate nginx
```

Para testar com 3 instancias:

```powershell
$env:NGINX_CONF="./nginx.conf"
docker-compose up -d --force-recreate nginx
```

### Rodar teste automatico e gerar CSV

Exemplo com 10 usuarios, taxa de subida de 10 usuarios por segundo e duracao de 1 minuto:

```powershell
docker-compose exec -e TARGET_PATHS="/?p=1" locust locust -f locustfile.py --host http://nginx --headless -u 10 -r 10 -t 1m --csv reports/cenario1_3wp_10users
```

Exemplos para os tres numeros de usuarios pedidos:

```powershell
docker-compose exec -e TARGET_PATHS="/?p=1" locust locust -f locustfile.py --host http://nginx --headless -u 10 -r 10 -t 1m --csv reports/cenario1_3wp_10users
docker-compose exec -e TARGET_PATHS="/?p=1" locust locust -f locustfile.py --host http://nginx --headless -u 100 -r 10 -t 1m --csv reports/cenario1_3wp_100users
docker-compose exec -e TARGET_PATHS="/?p=1" locust locust -f locustfile.py --host http://nginx --headless -u 1000 -r 50 -t 1m --csv reports/cenario1_3wp_1000users
```

Os arquivos `.csv` gerados na pasta `reports/` podem ser usados para montar os graficos do relatorio, comparando:

- tempo medio de resposta;
- requisicoes por segundo;
- falhas;
- percentis de resposta.

## Estrutura do Projeto

- **mysql-db**: contêiner do banco de dados MySQL com armazenamento persistente.
- **wordpress1, wordpress2, wordpress3**: três contêineres da aplicação WordPress.
- **nginx**: balanceador de carga responsável por distribuir as requisições entre as instâncias do WordPress utilizando o algoritmo **Round Robin**.
- **wordpress-net**: rede do tipo **bridge** utilizada para comunicação interna entre os contêineres.

## Pré-requisitos

Antes de executar o projeto, certifique-se de ter instalado em sua máquina:

- [Docker](https://www.docker.com/products/docker-desktop/)
- [Docker Compose](https://docs.docker.com/compose/)

## Como Executar com Docker Compose

1. Clone este repositório ou baixe os arquivos para uma pasta local.
2. Verifique se os arquivos `docker-compose.yml` e `nginx.conf` estão no mesmo diretório.
3. No terminal, execute o comando:

```bash
docker-compose up -d
```

## Para testar:

Digite no seu terminal "http://localhost"

OU

Digite no terminal:
```bash
curl -I http://localhost
```

## Como Fazer do Zero pelo CMD, sem Utilizar `docker-compose.yml`

### 1. Criar a rede Docker

Primeiro, crie uma rede isolada para que os contêineres possam se comunicar entre si:

```bash
docker network create wordpress-net
```

### 2. Criar o contêiner do MySQL

```bash
docker run -d --name mysql-db --network wordpress-net ^
  -e MYSQL_ROOT_PASSWORD=r00t ^
  -e MYSQL_DATABASE=wordpress ^
  -e MYSQL_USER=usr-wordpress ^
  -e MYSQL_PASSWORD=pwd-wordpress ^
  -v %cd%/mysql_data:/var/lib/mysql ^
  mysql:5.7
```

### 3. Subir as instâncias do WordPress

#### WordPress 1

```bash
docker run -d --name wordpress1 --network wordpress-net ^
  -v %cd%/html:/var/www/html ^
  -e WORDPRESS_DB_HOST=mysql-db ^
  -e WORDPRESS_DB_USER=usr-wordpress ^
  -e WORDPRESS_DB_PASSWORD=pwd-wordpress ^
  -e WORDPRESS_DB_NAME=wordpress ^
  wordpress:5.4.2-php7.2-apache
```

#### WordPress 2

```bash
docker run -d --name wordpress2 --network wordpress-net ^
  -v %cd%/html:/var/www/html ^
  -e WORDPRESS_DB_HOST=mysql-db ^
  -e WORDPRESS_DB_USER=usr-wordpress ^
  -e WORDPRESS_DB_PASSWORD=pwd-wordpress ^
  -e WORDPRESS_DB_NAME=wordpress ^
  wordpress:5.4.2-php7.2-apache
```

#### WordPress 3

```bash
docker run -d --name wordpress3 --network wordpress-net ^
  -v %cd%/html:/var/www/html ^
  -e WORDPRESS_DB_HOST=mysql-db ^
  -e WORDPRESS_DB_USER=usr-wordpress ^
  -e WORDPRESS_DB_PASSWORD=pwd-wordpress ^
  -e WORDPRESS_DB_NAME=wordpress ^
  wordpress:5.4.2-php7.2-apache
```

### 4. Subir o balanceador de carga com Nginx

```bash
docker run -d --name nginx -p 80:80 --network wordpress-net ^
  -v %cd%/nginx.conf:/etc/nginx/nginx.conf:ro ^
  -v %cd%/html:/usr/share/nginx/html ^
  nginx:1.19.0
```

### 5. Verificar se os contêineres estão rodando

```bash
docker ps
```

### 6. Parar e remover toda a infraestrutura

```bash
docker stop mysql-db wordpress1 wordpress2 wordpress3 nginx
docker rm mysql-db wordpress1 wordpress2 wordpress3 nginx
docker network rm wordpress-net
```

### 7. Realizar testes

#### Teste de conectividade

```bash
curl -I http://localhost
```

#### Verificar se os processos estão ativos

```bash
docker ps
```

#### Teste no navegador

Abra o navegador e acesse:

```bash
http://localhost
```

Se tudo estiver configurado corretamente, a aplicação WordPress deverá ser exibida.
