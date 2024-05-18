import subprocess
import sys

from config.config import config

EXIT_PATTERN = "SystemExit: "

show_text:str = ""
while True:
    main  = subprocess.Popen(
        ['python'] + [config['main']] + [show_text],
        executable=config['python_cmd'],
        stderr=subprocess.PIPE
        #creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    assert main.stderr is not None
    last_line:bytes = b''
    for line in iter(main.stderr.readline,b''):
        last_line = line
        sys.stderr.buffer.write(line)
    main.wait()
    last_line_text = last_line.decode()
    if EXIT_PATTERN in last_line_text:
        i = last_line_text.index(EXIT_PATTERN) + len(EXIT_PATTERN)
        exit_code = int(last_line_text[i:])
        match exit_code:
            case 0:#simple restart
                show_text = "The server has successfully restarted."
    else:
        show_text = f"The server shut down unexpectedly with the error:\n{last_line_text}"