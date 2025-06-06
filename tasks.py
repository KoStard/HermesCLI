from invoke import task


@task
def performance_test_with_import(c):
    c.run("uv run python -X importtime -m hermes.main")
