# Guide: Adding a New AI Module to the Ecosystem

Link Curator is designed so future autonomous AI modules (e.g. `modules/task_manager`, `modules/paper_researcher`, `modules/expense_tracker`) can be added without altering the core framework.

## Step-by-Step Instructions

### 1. Create Module Directory
Create a dedicated subfolder under `modules/`:
```
modules/<your_module_name>/
  ├── __init__.py
  ├── models.py       # Module database models (use prefix e.g. tm_ for task manager)
  ├── schemas.py      # Pydantic schemas
  ├── commands.py     # Command registration
  └── service.py      # Module core logic
```

### 2. Define Table Models with Namespace Prefix
In `modules/<your_module_name>/models.py`:
```python
from sqlalchemy import Column, Integer, String
from adapters.storage.base_model import Base

class CustomItem(Base):
    __tablename__ = "modname_items"  # ALWAYS prefix tables with your module name

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
```

### 3. Register Commands Using the Router Decorator
In `modules/<your_module_name>/commands.py`:
```python
from core.router import router, CommandContext

@router.register(
    name="mycmd",
    description="Deskripsi perintah baru",
    usage="/mycmd <arg>",
    module="my_module",
    aliases=["mc"]
)
async def handle_my_command(ctx: CommandContext) -> str:
    # ctx.sender -> WhatsApp sender number
    # ctx.args -> List of parsed arguments
    # ctx.text -> Raw argument string
    return f"Perintah modul dijalankan dengan argumen: {ctx.text}"
```

### 4. Hook into the Event Bus (Optional)
If your module reacts to system-wide events:
```python
from core.bus import bus

async def on_new_curation(data):
    # Process event
    pass

bus.subscribe("curation_completed", on_new_curation)
```

### 5. Register in Application Lifespan
Import your module's commands in `renderers/web_dashboard/app.py`:
```python
import modules.my_module.commands
```
Your new commands will automatically show up when users type `/bantuan`!
