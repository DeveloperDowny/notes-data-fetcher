from pydantic import BaseModel, Field
from typing import List, Optional

class Note(BaseModel):
    note: str = Field(alias="n_ans")
    note_images: Optional[List[str]] = Field(default=None, alias="n_imgs")
    
    @property
    def images(self):
        return ", ".join(self.note_images) if self.note_images else ""
    
    model_config = {
        "populate_by_name": True,
        # This allows using both original field names and aliases
    }