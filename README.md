# HAPE Framework: Build an Automation Tool With Ease

## For Users

### Installation
To install appname CLI, run:
```sh
make install
```

### Usage
To execute a command, use:
```sh
appname <command> [options]
```
Example:
```sh
appname --help
```

## For Developers

### Setup
1. Clone the repository:
   ```sh
   git clone <repo_url>
   ```
   
2. Rename hape-framework to your AppNameShort
   ```sh
   mv appname yourappname
   cd yourappname
   ./scripts/rename-hape-framework.sh
   ```

3. Create and activate a virtual environment:
   ```sh
   make init-dev

   ```
4. Create and activate a virtual environment:
   ```sh
   make init-dev
   ```
5. activate virtual environment venv
   ```sh
   source ./.scripts/start-venv.sh
   ```

### Running Tests
To execute tests for the executable run:
```sh
make run-test-container
```
```sh
make install
appname --version
```
To run the function playground() in src/controllers/appname_controller.py run
```
make run
```

### Database Migrations
1. Create a new migration:
   ```sh
   make create-migration
   ```
2. Apply migrations:
   ```sh
   make run-migration
   ```

### Publishing a New Version of CLI
To publish a new version:
```sh
make publish
```

### Project Overview
#### CLI Name
appname CLI
#### Primary Files
```
Makefile → Automates setup, testing, migrations, publishing.
README.md → Updated documentation for users & developers.
setup.py → Packaging configuration.
main.py → Entry point for CLI execution.
.env → Environment variables for database & configurations.
alembic.ini → Database migrations configuration.
```
#### Dependencies:
```
requirements-dev.txt (for development)
requirements-command.txt (for CLI commands)
```
#### Scripts:
```
.scripts/start-venv.sh → Starts the virtual environment.
.scripts/run-test-env.sh → Runs tests in a containerized environment.
```

### Build & Deployment
Uses Makefile to:
```
make install: Install.
make run-test-container: runs a python debian bookworm container for testing.
make publish: Build and Publish PYPI package to AWS CodeArtifact.
```

### Database & Migrations
Uses SQLAlchemy & Alembic for database schema management.
The Alembic environment (alembic.ini) is set up.
Tables are managed via models (likely under appname/src/models/).
#### Commands
```
make create-migration: generate new database migration files
make run-migration: run database migrations.
```