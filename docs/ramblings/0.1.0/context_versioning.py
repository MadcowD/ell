import inspect
import ast
from contextlib import contextmanager

@contextmanager
def context():
    # Get the current frame
    frame = inspect.currentframe()
    try:
        # Get the caller's frame
        caller_frame = frame.f_back.f_back
        # Get the filename and line number where the context manager is called
        filename = caller_frame.f_code.co_filename
        lineno = caller_frame.f_lineno

        # Read the source code from the file
        with open(filename, 'r') as f:
            source = f.read()

        # Parse the source code into an AST
        parsed = ast.parse(source, filename)
        # print(source)
        # Find the 'with' statement at the given line number
        class WithVisitor(ast.NodeVisitor):
            def __init__(self, target_lineno):
                self.target_lineno = target_lineno
                self.with_node = None

            def visit_With(self, node):
                if node.lineno <= self.target_lineno <= node.end_lineno:
                    self.with_node = node
                self.generic_visit(node)

        visitor = WithVisitor(lineno)
        visitor.visit(parsed)

        # print(parsed, source)
        if visitor.with_node:
            # Extract the source code of the block inside 'with'
            start = visitor.with_node.body[0].lineno
            end = visitor.with_node.body[-1].end_lineno
            block_source = '\n'.join(source.splitlines()[start-1:end])
            print("Source code inside 'with' block:")
            print(block_source)
        else:
            print("Could not find the 'with' block.")

        # Yield control to the block inside 'with'
        yield
    finally:
        # Any cleanup can be done here
        pass

from context_versioning import context
# Example usage
if __name__ == "__main__":
    with context():
        x = 10
        y = x * 2
        print(y)

        