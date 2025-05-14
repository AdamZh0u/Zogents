from pyzotero import zotero

from src.config import CONFIG

zot = zotero.Zotero(
    CONFIG["zotero"]["library_id"],
    CONFIG["zotero"]["library_type"],
    CONFIG["zotero"]["api_key"],
    # local=True
)  # local=True for read access to local Zotero
items = zot.top(limit=5)
# we've retrieved the latest five top-level items in our library
# we can print each item's item type and ID
for item in items:
    print("Item: %s | Key: %s" % (item["data"]["itemType"], item["data"]["key"]))

## get latest item from zotero
first_item = zot.top(limit=1)
key = first_item[0]["key"]
# file = zot.fulltext_item(key)
print(key)
