from ..models import SourceDefinition

SOURCE = SourceDefinition(
    id="bea",
    name="U.S. Bureau of Economic Analysis (BEA)",
    type="api",
    homepage="https://www.bea.gov/",
    notes="GDP, PCE, balance of payments via API.",
    requires={"BEA_API_KEY": "BEA API key"},
)
