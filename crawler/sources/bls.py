from ..models import SourceDefinition

SOURCE = SourceDefinition(
    id="bls",
    name="U.S. Bureau of Labor Statistics (BLS)",
    type="api",
    homepage="https://www.bls.gov/",
    notes="CPI, employment, wages via Public Data API.",
    requires={"BLS_API_KEY": "BLS API key"},
)
