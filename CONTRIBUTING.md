# Contributing

## Self-hosting
To host your own instance of AccountaBot:
1. Set-up an application on the [Discord developer portal](https://discord.com/developers/applications/).
2. Add a `.env` file in the root directory of the repository with your application ID.
    ```bash
    # in .env
    DISCORD_TOKEN=your-application-id
    ```
3. In the root directory of the repository, install the package locally (a virtual environment is recommended to avoid cluttering your Python installation).
    ```console
    $ pip install .
    ```
4. Run AccountaBot!
    ```console
    $ accountabot
    ```

## Developer Set-up
To set-up your development environment:
1. In the root directory of the repository, install the package locally (a virtual environment is recommended to avoid cluttering your Python installation). Use the `-e` flag to make an editable installation.
    ```console
    $ pip install . -e
    ```
2. Install developer requirements.
    ```console
    $ pip install -r requirements-dev.txt
    ```

## Linting and Pre-commit Hooks
Run linting by using the pre-commit module.
```console
$ pre-commit run --all-files
```
Pre-commit can also be installed to run automatically before commits
```console
$ pre-commit install
```
One of the hooks used by pre-commit runs `Pyright`. This can be installed through `node`, or the Python package version can be installed with `pip install pyright`.

## Testing
To run tests, simply run `pytest`.
To test-run a local version of AccountaBot, see [Self-Hosting](#self-hosting).
