# Email Circle
This is a clone of LetterLoop as a fun side project.

## Set up
### Requirements
- Docker Installed
- node v18 or greater
- yarn
### pyenv

1. Install and set-up pyenv from https://github.com/pyenv/pyenv?tab=readme-ov-file#installation
2. Install python version
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
There is a `pyproject.toml` file that will install local `dev` commands and requirements.
```
pip install -e .
```
or if you have `uv`
```
uv pip install -e .
```

## Development
### Running the server
```
dev compose up
```
API accessible and `localhost/api/v1/docs`
### Running the client
```
cd react
yarn run dev
```
Accessible at `localhost:5173`

## Deployment
### Build new images
```
dev compose any --prod build
```
### Push to registry
```
dev docker tp
```
### Deploy
- ssh into the server

```bash
cd ring
git pull
./dev_util/prod.sh
dev compose any --prod down worker beat
dev db upgrade
dev compose any --prod up -d
# may need to restart nginx
dev compose any --prod restart nginx
```