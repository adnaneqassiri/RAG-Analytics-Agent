from src.sandbox.runner import (
    PythonSandboxRunner,
)


runner = PythonSandboxRunner()


result = runner.run(
    columns=[
        "name",
        "total_sales",
    ],

    rows=[
        ["Alfred", 35826.99],
        ["John", 31200.50],
        ["Sara", 29100.00],
        ["Maria", 26750.40],
    ],

    code="""
print(df)

print(
    "\\nAverage sales:",
    df["total_sales"].mean()
)

sns.barplot(
    data=df,
    x="total_sales",
    y="name",
)

plt.title(
    "Customers by total sales"
)
""",
)


print(
    "RUN:",
    result.run_id
)

print(
    "STDOUT:"
)

print(
    result.stdout
)

print(
    "ARTIFACTS:"
)

for artifact in result.artifacts:
    print(
        artifact.name,
        artifact.mime_type,
        artifact.path,
    )