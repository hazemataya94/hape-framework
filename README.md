# HAPE Framework: Build an Automation Tool With Ease

# Overview
Nowadays we hear about Internal Development Platforms everywhere, and we strive to build a customized Platform that integrates with all the tools required for a DevOps or Platform engineer to guarantee a high-performing infrastructure to enable rapid software development process. However, building a platform requires a lot of effort to integrate with a variety of tools, each with its own state, different syntax and language. 

The available platforms in the market target general solutions, and require a subsicription for something that can't be modified. The market has no framework -yet- to help you build your own platform to solve your own use-cases. 

HAPE Framework aims to fill the gap in the market, and provide a framework to simplify the work of Infrastructure and Automation management by enabling engineers to build a personlized centralized solution, customized to fulfill different use-cases each time. 

At the moment it's still in very early stages, but there is a lot of potential to build a framework that benifits everyone. 

If you're interested in contributing feel free to email the Author. 

Hazem Ataya: hazem.ataya94@gmail.com

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

# Author
Hazem Ataya: hazem.ataya94@gmail.com