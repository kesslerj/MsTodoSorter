# MS Todo Einkaufsliste sortieren

## Run

File `.env`:

    ACCESS_TOKEN=...
    LIST_ID=...

### Windows
- `Aus Graph Explorer `ACCESS_TOKEN` kopieren
    - https://developer.microsoft.com/en-us/graph/graph-explorer
    - GET https://graph.microsoft.com/beta/me/outlook/taskFolders('AQMkADAwATE0OTYwLTQ4NzcALTdhY2QtMDACLTAwCgAuAAADRRw4fksEhU_rrF0G0-jTIQEApPXHxG5mgEmOIhc1S1OS_gAI6UHhwgAAAA==')/tasks
    - Permissions: Task.Read und Tasks.ReadWrite (dafür auf POST umstellen)
    - 
- Ausführen:`python sort_todos.py`



## Todos
- Dokumentieren, wo die List-Id herkommt
- Einfachere Authentifizierung als Access-Token kopieren
- auf dem Handy lauffähig machen