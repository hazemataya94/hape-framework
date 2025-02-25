DOCKERFILE_DEV = """
FROM python:3.12-bookworm

WORKDIR /workspace

COPY . /workspace

WORKDIR /workspace/playground

ENTRYPOINT ["sleep", "infinity"]
""".strip()

DOCKERFILE_PROD = """
FROM python:3.12-bookworm

RUN pip install --upgrade {{project_name}}

ENTRYPOINT ["{{project_name}}"]
""".strip()


DOCKER_COMPOSE = """
services:
  {{project_name}}:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: {{project_name}}
    restart: always
    env_file:
      - ../.env
    environment:
      HAPE_MARIADB_HOST: "host.docker.internal"
    networks:
      - host_network

  mariadb:
    image: mariadb:11.4.4
    container_name: mariadb_dev
    restart: always
    environment:
      MARIADB_ROOT_PASSWORD: root
      MARIADB_DATABASE: {{project_name_snake_case}}_db
      MARIADB_USER: {{project_name_snake_case}}_user
      MARIADB_PASSWORD: {{project_name_snake_case}}_password
    ports:
      - "3306:3306"
    networks:
      - host_network
    volumes:
      - mariadb_data:/var/lib/mysql
      - ./mariadb-init:/docker-entrypoint-initdb.d

  phpmyadmin:
    image: phpmyadmin/phpmyadmin
    container_name: phpmyadmin_dev
    restart: always
    environment:
      PMA_HOST: host.docker.internal
      PMA_PORT: 3306
    ports:
      - "8080:80"
    networks:
      - host_network

networks:
  host_network:
    driver: bridge

volumes:
  mariadb_data:
""".strip()