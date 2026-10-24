import sys

from ai_email_ops.app.knowledge import ingest_folder

organization_id = int(sys.argv[1])
folder = sys.argv[2]
count = ingest_folder(organization_id, folder)
print(f"Ingested {count} files for organization {organization_id}")