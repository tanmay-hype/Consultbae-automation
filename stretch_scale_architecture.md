# Task 5: 5,000 Worker Scale-Up Architecture

If this audio collection app is launched to 5,000 gig workers over a single weekend, the current SQLite/synchronous architecture will face critical bottlenecks. 

### What Breaks First?
1. **Server Thread Exhaustion:** Handling 5,000 concurrent multi-megabyte audio file uploads will lock up the FastAPI synchronous worker threads, leading to high memory spikes and 504 Gateway Timeouts.
2. **CPU Starvation:** Running Librosa digital signal processing (DSP) calculations synchronously on the web server blocks the event loop entirely.
3. **Database Locking:** If reverting to SQLite, concurrent writes will trigger database lock errors. Unpooled PostgreSQL connections will max out the active client limits.

### Architectural Mitigations Before Launch
1. **Direct-to-Cloud Storage (S3 Pre-Signed URLs):** The web server should never handle raw audio binaries. The frontend must request an AWS S3 pre-signed URL from FastAPI and upload the audio directly to the bucket. This reduces server bandwidth and memory utilization to near zero.
2. **Asynchronous Task Queues:** An S3 `ObjectCreated` trigger should push an event into a message broker (Redis/RabbitMQ). A fleet of background Celery workers will pick up the task, run the heavy `librosa` DSP extraction, and update the database asynchronously.
3. **Database Connection Pooling:** Implement PgBouncer in front of the PostgreSQL instance to multiplex thousands of incoming backend connections into a small, manageable pool of active database connections.
4. **Idempotency & Duplicate Protection:** Implement a Redis-backed distributed lock utilizing the worker's 10-digit phone number to prevent rapid, accidental multi-submission clicks from generating duplicate DSP tasks.