from invoke import task

@task
def performance_test_with_import(c):
    result = c.run("uv run python -X importtime -c \"from hermes import main\" 2> importtime.txt")
    if result.ok:
        print("Import time test results captured in importtime.txt.")
