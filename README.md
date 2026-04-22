# Projeto: Arquitetura de Alta Disponibilidade (WordPress + Nginx)

Este projeto consiste em uma infraestrutura escalável utilizando Docker, composta por um banco de dados MySQL centralizado, três instâncias de aplicação WordPress e um balanceador de carga Nginx para distribuição de tráfego.

## Estrutura do Projeto
- **mysql-db**: Banco de dados MySQL (armazenamento persistente).
- **wordpress1, wordpress2, wordpress3**: Três contêineres de aplicação WordPress (PHP 7.2 + Apache).
- **nginx**: Balanceador de carga configurado para distribuir requisições usando o algoritmo *Round Robin*.
- **Rede**: `wordpress-net` (Bridge) isolando os serviços.

## Pré-requisitos
Certifique-se de ter instalado em sua máquina:
- [Docker](https://www.docker.com/products/docker-desktop/)
- [Docker Compose](https://docs.docker.com/compose/)

## Como Executar
1. Clone este repositório ou baixe os arquivos para uma pasta local.
2. Certifique-se de que os arquivos `docker-compose.yml` e `nginx.conf` estejam no mesmo diretório.
3. No terminal, execute o comando:
   ```bash
   docker-compose up -d


### Como fazer "do zero" através do cmd, sem utilizar docker-compose.yml
1. Primeiro, precisamos criar uma rede isolada para que os containers conversem entre si:
   'docker network create wordpress-net'

2. Execute o container do mysql: docker run -d --name mysql-db --network wordpress-net ^
  -e MYSQL_ROOT_PASSWORD=r00t ^
  -e MYSQL_DATABASE=wordpress ^
  -e MYSQL_USER=usr-wordpress ^
  -e MYSQL_PASSWORD=pwd-wordpress ^
  -v %cd%/mysql_data:/var/lib/mysql ^
  mysql:5.7

3. Subir as instâncias do wordpress:
'WordPress 1'
docker run -d --name wordpress1 --network wordpress-net ^
  -v %cd%/html:/var/www/html ^
  -e WORDPRESS_DB_HOST=mysql-db ^
  -e WORDPRESS_DB_USER=usr-wordpress ^
  -e WORDPRESS_DB_PASSWORD=pwd-wordpress ^
  -e WORDPRESS_DB_NAME=wordpress ^
  wordpress:5.4.2-php7.2-apache

'WordPress 2'
docker run -d --name wordpress2 --network wordpress-net ^
  -v %cd%/html:/var/www/html ^
  -e WORDPRESS_DB_HOST=mysql-db ^
  -e WORDPRESS_DB_USER=usr-wordpress ^
  -e WORDPRESS_DB_PASSWORD=pwd-wordpress ^
  -e WORDPRESS_DB_NAME=wordpress ^
  wordpress:5.4.2-php7.2-apache

'WordPress 3'
docker run -d --name wordpress3 --network wordpress-net ^
  -v %cd%/html:/var/www/html ^
  -e WORDPRESS_DB_HOST=mysql-db ^
  -e WORDPRESS_DB_USER=usr-wordpress ^
  -e WORDPRESS_DB_PASSWORD=pwd-wordpress ^
  -e WORDPRESS_DB_NAME=wordpress ^
  wordpress:5.4.2-php7.2-apache

4. subir o balanceamento de carga (nginx)
docker run -d --name nginx -p 80:80 --network wordpress-net ^
  -v %cd%/nginx.conf:/etc/nginx/nginx.conf:ro ^
  -v %cd%/html:/usr/share/nginx/html ^
  nginx:1.19.0

5. para verificar  es estão rodando:
docker ps

6. para parar e remover tudo:
docker stop mysql-db wordpress1 wordpress2 wordpress3 nginx
docker rm mysql-db wordpress1 wordpress2 wordpress3 nginx
docker network rm wordpress-net

7. para testes
teste de conectividade:
curl -I http://localhost 

testar se os processos estão vivos:
docker ps

testar no navegador, você deve apenas abrir o browser e digitar "http://localhost"