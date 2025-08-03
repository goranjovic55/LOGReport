import ast

with open('src/commander/ui/commander_window.py', 'r') as f:
    content = f.read()

tree = ast.parse(content)
imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]

print(f'Number of imports: {len(imports)}')
for node in imports:
    print(f'  {ast.unparse(node)}')