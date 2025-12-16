# ai generated

import asyncio
import random
import time


async def producer(queue):
    print(f"👨‍🍳 PRODUCER: Starting to add jobs...\t\t {time.perf_counter()-start:.2f}")
    for i in range(5):
        # Simulating work to create the job
        await asyncio.sleep(1)
        item = f"Job-{i}"
        await queue.put(item)
        print(f"    --> Added {item}\t\t {time.perf_counter()-start:.2f}")
    print(f"👨‍🍳 PRODUCER: All jobs added. I am done.\t\t {time.perf_counter()-start:.2f}")


async def consumer(queue, worker_id):
    print(f"    🤖 WORKER {worker_id}: Online\t\t {time.perf_counter()-start:.2f}")
    while True:
        # 1. Wait for a job
        item = await queue.get()

        # 2. Process the job
        print(f"    🤖 WORKER {worker_id}: Processing {item}...\t\t {time.perf_counter()-start:.2f}")
        # duration = random.uniform(1.0, 2.0)
        duration = 3
        await asyncio.sleep(duration)

        # 3. Mark as done (CRITICAL STEP)
        print(f"    ✅ WORKER {worker_id}: Finished {item}\t\t {time.perf_counter()-start:.2f}")
        queue.task_done()


async def main():
    queue = asyncio.Queue()

    # 1. Start the consumers (They will sit and wait for data)
    workers = [asyncio.create_task(consumer(queue, i)) for i in range(2)]

    # 2. Start the producer (It will start feeding data)
    producer_task = asyncio.create_task(producer(queue))

    # 3. Wait for the producer to finish putting everything
    await producer_task

    # 4. Wait for the queue to be empty (Internal Counter == 0)
    print(f"🛑 MAIN: Waiting for queue to drain...\t\t {time.perf_counter()-start:.2f}")
    await queue.join()

    # 5. Cancel the workers (They are stuck in 'while True')
    for w in workers:
        w.cancel()

    print(f"🎉 MAIN: All done.\t\t {time.perf_counter()-start:.2f}")


if __name__ == "__main__":
    start = time.perf_counter()
    asyncio.run(main())