import ell

ERROR = """
PS C:\\Users\\Bob> curl -sSL https://install.python-poetry.org | python3 -
Invoke-WebRequest : A parameter cannot be found that matches parameter name 'sSL'.
At line:1 char:6
+ curl -sSL https://install.python-poetry.org | python3 -
+      ~~~~
    + CategoryInfo          : InvalidArgument: (:) [Invoke-WebRequest], ParameterBindingException
    + FullyQualifiedErrorId : NamedParameterNotFound,Microsoft.PowerShell.Commands.InvokeWebRequestCommand

PS C:\\Users\\Bob>
"""


@ell.lm(model="gpt-4o-mini", temperature=1.0)
def fix_error(error) -> str:
    """You are helping me set up a project repo that uses poetry and python."""
    return "diagnose my error" + error


if __name__ == "__main__":
    ell.config.verbose = True
    from ell.stores.sql import SQLiteStore

    ell.set_store(SQLiteStore("sqlite_example"), autocommit=True)

    print(fix_error(ERROR))
