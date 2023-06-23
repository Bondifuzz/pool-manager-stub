# Pool manager

## Deployment

Download repository

```bash
git clone https://github.com/Bondifuzz/pool-manager.git
cd pool-manager
```

Build docker image

```bash
docker build -t bondifuzz/pool-manager .
```

Run container (locally)

```bash
docker run --net=host --rm -it --name=pool-manager --env-file=.env -v ~/.kube/config:/root/.kube/config bondifuzz/pool-manager bash
```

## Local development

### Clone pool-manager repository

All code and scripts are placed to pool-manager repository. Let's clone it.

```bash
git clone https://github.com/Bondifuzz/pool-manager.git
cd pool-manager
```

### Start services pool-manager depends on

Then you should invoke `docker-compose` to start all services pool-manager depends on.

```bash
ln -s local/dotenv .env
ln -s local/docker-compose.yml docker-compose.yml
docker-compose -p pool_manager up -d
```

### Verify access to Kubernetes cluster

Ensure you have an access to local/remote kubernetes cluster and have an appropriate config in `~/.kube` folder. Use commands like `kubectl get namespaces`, `kubectl get pods` to ensure all is ok.

### Run pool-manager

Finally, you can run pool-manager service:

```bash
# Install dependencies
pip3 install -r requirements-dev.txt

# Run service
python3 -m uvicorn \
    --factory pool_manager.app.main:create_app \
    --host 127.0.0.1 \
    --port 8080 \
    --workers 1 \
    --log-config logging.yaml \
    --lifespan on
```

### Code documentation

TODO

### Running tests

```bash
# Install dependencies
pip3 install -r requirements-test.txt

# Run unit tests
pytest -vv api-gateway/tests/unit

# Run functional tests
pytest -vv api-gateway/tests/integration
```

### Spell checking

Download cspell and run to check spell in all sources

```bash
sudo apt install nodejs npm
sudo npm install -g cspell
sudo npm install -g @cspell/dict-ru_ru
cspell link add @cspell/dict-ru_ru
cspell "**/*.{py,md,txt}"
```

### VSCode extensions

- `ms-python.python`
- `ms-python.vscode-pylance`
- `streetsidesoftware.code-spell-checker`
- `streetsidesoftware.code-spell-checker-russian`
