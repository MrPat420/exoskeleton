from typing import List
from pydantic import BaseModel, Field

class MarkdownTable(BaseModel):
    title: str = Field(description="Title of the structured data table")
    headers: List[str] = Field(description="Column headers")
    rows: List[List[str]] = Field(description="Data rows mapping to headers")

class RCALogic(BaseModel):
    symptom: str = Field(description="Observed system or cognitive failure")
    cause: str = Field(description="Verified root cause of the symptom")
    action_items: List[str] = Field(description="Ordered list of execution steps")

class EnforcedScaffoldResponse(BaseModel):
    headers: List[str] = Field(description="Structural section headers for Markdown output")
    rca_blocks: List[RCALogic] = Field(description="Root Cause Analysis structural blocks")
    tables: List[MarkdownTable] = Field(description="Spatial data matrices")
    bullet_points: List[str] = Field(description="High-density analytical vectors")

class DS00Record(BaseModel):
    record_id: str
    timestamp: str
    origin_source: str
    technical_metadata: List[str]
    content_matrix: EnforcedScaffoldResponse
