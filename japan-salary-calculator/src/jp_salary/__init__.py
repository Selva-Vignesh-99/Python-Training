"""Japanese salary deduction calculator."""
from .calculator import calculate
from .models import SalaryInput, SalaryResult

__all__ = ["calculate", "SalaryInput", "SalaryResult"]
