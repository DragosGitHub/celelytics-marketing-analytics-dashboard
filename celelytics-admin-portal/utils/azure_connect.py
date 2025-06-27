import os
from dotenv import load_dotenv
from azure.data.tables import TableServiceClient
from azure.core.credentials import AzureNamedKeyCredential
from datetime import timezone
import pytz

# ✅ Load environment variables from .env
load_dotenv()

account_name = os.getenv("ACCOUNT_NAME")
account_key = os.getenv("ACCOUNT_KEY")
table_name = os.getenv("TABLE_NAME", "contacts")

# 🛡️ Credential check
if not account_name or not account_key:
    raise ValueError("❌ ACCOUNT_NAME or ACCOUNT_KEY is missing in .env file.")

# ✅ Azure Table client setup
credential = AzureNamedKeyCredential(account_name, account_key)
service = TableServiceClient(
    endpoint=f"https://{account_name}.table.core.windows.net",
    credential=credential
)
table_client = service.get_table_client(table_name)

# ✅ Retrieve all messages
def get_all_messages():
    entities = list(table_client.list_entities())
    messages = []
    for entity in entities:
        name = entity.get("Name", "")
        email = entity.get("Email", "")
        message = entity.get("Message", "")
        partition_key = entity.get("PartitionKey", "")
        row_key = entity.get("RowKey", "")

        timestamp = entity.metadata.get("timestamp", "")
        date_str, time_str = "", ""

        if timestamp:
            local_tz = pytz.timezone("Asia/Kolkata")
            local_time = timestamp.replace(tzinfo=timezone.utc).astimezone(local_tz)
            date_str = local_time.strftime("%Y-%m-%d")
            time_str = local_time.strftime("%H:%M:%S")  # 24-hour format

        messages.append({
            "name": name,
            "email": email,
            "message": message,
            "date": date_str,
            "time": time_str,
            "partition_key": partition_key,
            "row_key": row_key
        })
    return messages

# ✅ Delete messages using PartitionKey & RowKey
def delete_messages_by_info(message_list):
    success_count = 0
    for msg in message_list:
        pk = msg.get("partition_key")
        rk = msg.get("row_key")

        if not pk or not rk:
            continue

        try:
            table_client.delete_entity(partition_key=pk, row_key=rk)
            success_count += 1
        except Exception as e:
            print(f"❌ Failed to delete message: {pk} | {rk} → {e}")

    return success_count == len(message_list)
