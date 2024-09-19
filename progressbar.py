from rich import print
import time


def progress_bar(current, total, bar_length=20):
    current += 1
    percent = round(float(current) * 100 / total, 1)
    arrow = "-" * int(percent / 100 * bar_length - 1) + ">"
    spaces = " " * (bar_length - len(arrow))
    if not current == total:
        print(
            f"[bold yellow]Progress[/bold yellow]: [{arrow}{spaces}] {percent}% [{current}/{total}]",
            end="\r",
        )
    else:
        print(
            f"[bold green]Complete: [------------------->] 100 % [{current}/{total}][/bold green]"
        )

def cycling_progress(mirror_is_running):
    if mirror_is_running:
        bar_length = 20
        for i in range(bar_length):
            cycle = "." * i
            space = " " * int(bar_length - i)
            print(f"[bold yellow]Processing[/bold yellow]: \[{cycle}{space}]" , end="\r") 
            time.sleep(0.3)
    else:
        print("[bold green]Complete: \[....................][/bold green]")


# mirror_is_running = True
# cycling_progress(mirror_is_running)