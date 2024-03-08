from rich import print


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
