from pathlib import Path
Path('observation.txt').write_text('unicode α\n')
print('r62-recorder-start\n' + 'z' * 40000 + '\nr62-recorder-end')
