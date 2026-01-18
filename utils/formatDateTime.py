from datetime import datetime

def format_datetime(value):
    if not value:
        return "NULL"

    # Convert to datetime if string
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))

    return value.strftime("%d %B %Y, %I:%M %p")

# q = ["2026-01-17 17:36:04.936841", 
# "2026-01-17 18:16:02.411022+00:00",
# "2026-01-12 05:53:46"]
# for i in q:
#     print(format_datetime(i))
