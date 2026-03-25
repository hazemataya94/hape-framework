name: {{ workflow_name }}

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t docker.io/CHANGE_ME/{{ app_name }}:${{ github.sha }} .
      - name: Print image reference
        run: echo "Built docker.io/CHANGE_ME/{{ app_name }}:${{ github.sha }}"
