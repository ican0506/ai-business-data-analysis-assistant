from app.analysis_modules.base import AnalysisCapability, AnalysisModule
from app.analysis_modules.generic import GenericModule
from app.analysis_modules.order import OrderModule
from app.analysis_modules.registry import ModuleRegistry
from app.analysis_modules.student_score import StudentScoreModule

__all__ = (
    "AnalysisCapability",
    "AnalysisModule",
    "GenericModule",
    "ModuleRegistry",
    "OrderModule",
    "StudentScoreModule",
)
