
import os, sys
for root, dirs, files in os.walk('c:\\Users\\damik\\Downloads\\MyFYP\\IRP\\Backend'):
  for file in files:
    if file.endswith('.py'):
      filepath = os.path.join(root, file)
      with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
          if 'state.phase' in line and '=' in line:
            print(f'{filepath}:{i+1}:{line.strip()}')
