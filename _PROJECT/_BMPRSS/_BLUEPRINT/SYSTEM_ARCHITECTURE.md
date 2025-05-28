
---

### 2. System Architecture 
**Path:** `_BMPRSS/_BLUEPRINT/SYSTEM_ARCHITECTURE.md`
```markdown
# LOGReport System Architecture

## Component Diagram
```plantuml
@startuml
[Log Files] --> [Folder Scanner]
[Folder Scanner] --> [Text Processor]
[Text Processor] --> [PDF Generator]
[Text Processor] --> [DOCX Generator]
[PDF Generator] --> [Output PDF]
[DOCX Generator] --> [Output DOCX]

note right of [Folder Scanner]
  Recursive directory traversal
  with file filtering
end note
@enduml