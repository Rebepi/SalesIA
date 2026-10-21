from typing import Literal, Optional

from pydantic import BaseModel, Field


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=64)
    ui_theme: Optional[str] = Field(default=None, pattern="^(light|dark)$")
    ui_density: Optional[str] = Field(default=None, pattern="^(comfortable|compact)$")
    reduced_motion: Optional[bool] = None
    font_scale: Optional[str] = Field(default=None, pattern="^(small|standard|large)$")
    contrast_mode: Optional[str] = Field(default=None, pattern="^(standard|high)$")
    default_page_size: Optional[Literal[10, 25, 50, 100]] = None
    sidebar_mode: Optional[str] = Field(default=None, pattern="^(expanded|collapsed)$")
    accessible_tables: Optional[bool] = None
    toast_position: Optional[str] = Field(default=None, pattern="^(top-center|top-right|bottom-right)$")
