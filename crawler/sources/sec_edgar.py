from ..models import SourceDefinition

SOURCE = SourceDefinition(
    id="sec_edgar",
    name="SEC EDGAR",
    type="api",
    homepage="https://www.sec.gov/edgar",
    notes="10-K/10-Q/8-K filings via official API.",
    requires={"SEC_USER_AGENT": "SEC required User-Agent"},
)
