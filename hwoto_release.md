## How to release a new version on PyPi

1. Ensure a new version number is set in `pyproject.toml`.

2. Create and push a fresh tag:
   ```
   git tag -s -a v1.0.2 -m "Release adapting to Indico 3.3.4 and new build system"
   git push --tags
   ```

3. Clean up:
    ```
    rm -rf venv
    rm dist/*
    ```
4. Create a fresh `venv` and activate it:
    ```
    python -m venv venv
    source venv/bin/activate
    ```

5. Install the plugin and build tooling inside, and build:
   ```
    python -m pip install -e .
    python -m pip install build
    python -m build
    ```

6. Assuming you have `twine` already on your system and have API keys at hand, check and upload the packages:
    ```
    twine check dist/*
    twine upload -r testpypi dist/*
    twine upload dist/*
    ```
7. After the release, bump the version number in `pyproject.toml` to allow for future developments.
