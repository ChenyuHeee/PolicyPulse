from ..models import SourceDefinition

SOURCE = SourceDefinition(
    id="fred",
    name="FRED Economic Data",
    type="api",
    homepage="https://fred.stlouisfed.org/",
    notes="Macro time series via official API.",
    requires={"FRED_API_KEY": "FRED API key"},
)
