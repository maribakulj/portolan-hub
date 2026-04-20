# portolan-sdk

Python SDK and CLI (`portolan`) for Portolan Hub. Populated in Sprint 4.

Planned surface (excerpt):

```python
from portolan import Client

client = Client(base_url="http://localhost:8000", token="...")
for r in client.query("Gustave Moreau", sources=["gallica"]).stream():
    print(r.title)
```

And the CLI:

```bash
portolan sources list
portolan query "Gustave Moreau" --sources gallica --output csv
```
