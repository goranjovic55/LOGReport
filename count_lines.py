with open('src/commander/ui/commander_window.py', 'r') as f:
    lines = f.readlines()

in_class = False
count = 0
for line in lines:
    if line.startswith('class CommanderWindow'):
        in_class = True
        count += 1
        continue
    if in_class:
        if line.startswith('class ') and not line.startswith('class CommanderWindow'):
            break
        if line.startswith('    ') or line.startswith('\t') or line.strip() == '':
            count += 1

print(f'CommanderWindow class lines: {count}')