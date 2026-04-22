# Projeto: Arquitetura de Alta Disponibilidade com WordPress e Nginx

Este projeto implementa uma infraestrutura escalável com Docker, composta por um banco de dados MySQL centralizado, três instâncias da aplicação WordPress e um balanceador de carga Nginx para distribuir o tráfego entre os serviços.

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