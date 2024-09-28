# Email Circle
This is a clone of LetterLoop as a fun side project.

## Set up
### Requirements
- Docker or Orbstack Installed
- node v18 or greater
- yarn
- any python virtual environment solution (e.g. pyenv, conda)
#### pyenv

1. Install and set-up pyenv from https://github.com/pyenv/pyenv?tab=readme-ov-file#installation
2. Install pyenv-virtualenv from https://github.com/pyenv/pyenv-virtualenv
3. Install python version
```
pyenv install 3.12.1
```
3. Create pyenv virtualenv
```
pyenv virtualenv 3.12.1 ring
```
4. Activate
```
pyenv activate ring
```

### Install
There is a `pyproject.toml` file that will install local `ring` commands and requirements.
```
pip install -e .
```
or if you have `uv`
```
uv pip install -e .
```

### `env` set up
Add a `.env` file with the following:
```
ENVIRONMENT=LOCAL
API_PORT=8001
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
SQLALCHEMY_DATABASE_URI=postgresql://ring-postgres:ring-postgres@db:5432/ring
JWT_SIGNING_ALGORITHM=HS256
VITE_API_URL=http://localhost
BACKEND_CORS_ORIGINS=http://localhost:5173
```
We'll need a `JWT_SIGNING_KEY` as well which can be generated with `openssl`
```
echo "JWT_SIGNING_KEY=$(openssl rand -hex 32)" >> .env
```
If you have `oh-my-zsh` set up, you can use the `dotenv` plugin to automatically load the `.env` file into the shell.

## Development
### Running the server
```
ring compose up
```
API accessible and `localhost/api/v1/docs`
### Running the client
```
cd react
yarn run dev
```
Accessible at `localhost:5173`

### `ring` commands
```
Usage: ring [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  compose
  db
  docker
  run
```
#### `ring compose`
A wrapper around docker compose. By default it will use the compose.dev.yml and always build the images. Pass --prod to use the compose.prod.yml file.
```
Usage: ring compose [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  any
  ps
  up
```

#### `ring db`
Entrypoint to working with the database. Can open pgcli or run migrations.
```
Usage: ring db [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  alembic
  generate
  pgcli
  upgrade
```

#### `ring docker`
Entrypoint to working with the docker registry. Can tag and push images to the registry.
```
Usage: ring docker [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  push
  tag
  tp
```

#### `ring run`
Run scripts or start a shell.
```
Usage: ring run [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  script
  shell
```

## Deployment
### Build new images
```
ring compose any --prod build
```
### Push to registry
```
ring docker tp
```
### Deploy
- ssh into the server

```bash
cd ring
git pull
./dev_util/prod.sh
ring db upgrade
ring compose any --prod up -d
# may need to restart nginx
ring compose any --prod restart nginx
```
