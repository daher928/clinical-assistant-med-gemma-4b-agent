"""
Clinical Assistant Agent - Tools Package

This package contains tools for accessing various medical data sources:
- ehr: Electronic Health Records
- labs: Laboratory results
- meds: Medication information
- imaging: Imaging reports
- ddi: Drug-Drug Interaction checker
- guidelines: Clinical guidelines
"""

from .ehr import get_ehr
from .labs import get_labs
from .meds import get_meds
from .imaging import get_imaging
from .ddi import query_ddi
from .guidelines import search_guidelines

__all__ = [
    'get_ehr',
    'get_labs',
    'get_meds',
    'get_imaging',
    'query_ddi',
    'search_guidelines',
]

