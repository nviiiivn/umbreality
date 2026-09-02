"""Company Sub-Stacks — Russian Doll nesting for every company.
Each company gets its own miniature stack: Sub-Throne, Sub-Messiah,
Sub-Temple, Sub-Illuminati. The global stacks can override sub-decisions."""

from .throne import SubThrone
from .messiah import SubMessiah
from .temple import SubTemple
from .illuminati import SubIlluminati


def for_company(company_name: str) -> dict:
    """Get the full sub-stack for a company."""
    return {
        "throne": SubThrone(company_name),
        "messiah": SubMessiah(company_name),
        "temple": SubTemple(company_name),
        "illuminati": SubIlluminati(company_name),
    }
