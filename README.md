# ConsultBae AI Automation Assignment

This repository contains the end-to-end data pipeline, n8n automation, and full-stack DSP audio extraction web app for the ConsultBae technical assessment.

## Setup Instructions
1. Clone the repository and add your `.env` file containing the `POSTGRES` credentials and `DATABASE_URL`.
2. Start the containerized infrastructure:
   `docker-compose up --build -d`
3. Execute the data ingestion and deduplication pipeline:
   `docker exec -it consultbae_api python -m pipeline.ingest`
4. Access the Audio DSP portal at `http://localhost:8000`.
5. Access n8n at `http://localhost:5678`, import `automation/n8n_pipeline_workflow.json`, and link your database credentials.

## Task 4: Data Issues Report
During the ingestion of the three provided CSV files, the following anomalies were resolved:
* **Inconsistent Phone Formats:** Mixed usages of `+91`, leading zeros, and spaces. Resolved by stripping non-numeric characters and enforcing a strictly validated 10-digit primary identifier.
* **Shifted Data Columns:** `source2_gig_workers.csv` contained a row where email was in the skills column and name was in the rate column. Resolved by engineering a schema validation check that realigned misplaced strings containing `@`.
* **Conflicting Experience Metrics:** Experience was denoted in months ("48 months") or text ("Fresher"). Resolved via a regex normalizer that converted all formats into fractional years.
* **Missing Contact Fields:** `source3_cbnexus_contacts.csv` frequently omitted phone numbers. Resolved by implementing a 3-tier waterfall entity resolution (Phone -> Email -> Fuzzy Name/Location) to ensure accurate candidate merging without data loss.

## Stuck Log
* **Docker Network Race Conditions:** I initially hardcoded the API to connect to PostgreSQL on boot. Because Postgres takes ~5 seconds to initialize, the FastAPI container crashed with `Connection refused`. I resolved this by manually staging the boot sequence (`docker-compose up -d db` first), and eventually migrating the credentials to a secure `.env` file.
* **Browser Audio Codec Bitrate Computation:** The `MediaRecorder` API defaults to `.webm` containers, making standard WAV header parsing fail when extracting audio bitrates. I unstuck myself by researching the `soundfile` and `librosa` documentation to extract the true byte length dynamically against the analyzed frame duration.