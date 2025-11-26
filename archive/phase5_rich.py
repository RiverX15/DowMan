# ai generated

import asyncio
import random
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn


# A simulated async worker
async def download_file(task_id: int, file_name: str, progress: Progress):
    """
    Simulates downloading a file by sleeping.
    Updates the shared progress bar instance.
    """
    total_size = 100

    # Simulate work in chunks
    while not progress.finished:
        # Simulate network latency (I/O operation)
        await asyncio.sleep(random.uniform(0.05, 0.2))

        # Advance the progress bar for this specific task
        # .advance() is thread-safe and fast, so it's safe to call here
        progress.advance(task_id, advance=random.randint(1, 10))

        # Check if this specific task is done (Rich handles this logic internally too)
        current_completed = progress.tasks[task_id].completed
        if current_completed >= total_size:
            break


async def main():
    # Define the columns you want in your progress bar
    # This setup looks like: [Spinner] [Filename] [Bar] [Percentage] [Time Remaining]
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
    ) as progress:
        # 1. Create tasks in the progress bar first to get their IDs
        task1 = progress.add_task("[red]Downloading kernel...", total=100)
        task2 = progress.add_task("[green]Downloading assets...", total=100)
        task3 = progress.add_task("[cyan]Downloading ui_data...", total=100)

        # 2. Schedule the async work, passing the progress instance and task IDs
        await asyncio.gather(
            download_file(task1, "kernel", progress),
            download_file(task2, "assets", progress),
            download_file(task3, "ui_data", progress)
        )


if __name__ == "__main__":
    asyncio.run(main())