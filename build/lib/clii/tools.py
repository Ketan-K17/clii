import time
import subprocess
import os

def type_print(answer: str, delay: float = 0.03):
    step = 3
    for i in range(0, len(answer), step):
        print(answer[i:i + step], end="", flush=True)
        time.sleep(delay)
    print()


def type_command(text: str):
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "type_command.sh")
    subprocess.run(["bash", script, text], check=True)


if __name__ == "__main__":
    type_command("ls -a | grep 'sanity'")
