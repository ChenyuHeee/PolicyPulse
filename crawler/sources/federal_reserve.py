from ..models import SourceDefinition

SOURCE = SourceDefinition(
    id="federal_reserve",
    name="Federal Reserve (FOMC/Press)",
    type="rss",
    homepage="https://www.federalreserve.gov/",
    notes="Statements, minutes, speeches, and press releases.",
)
