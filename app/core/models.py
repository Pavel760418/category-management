from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class UploadIssue(BaseModel):
    severity: str
    message: str
    column: Optional[str] = None


class FileStatus(BaseModel):
    file_name: str
    template_type: str
    loaded: bool = False
    mapped: bool = False
    valid: bool = False
    issues: List[UploadIssue] = Field(default_factory=list)


class KPIResult(BaseModel):
    code: str
    name: str
    actual: Optional[float] = None
    target: Optional[float] = None
    ratio: Optional[float] = None
    status: str = "Недоступно"
    direction: str = "up"


class AnalysisContext(BaseModel):
    category_name: str = "Товары для животных"
    category_role: str = "routine"
    loaded_files: Dict[str, bool] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
