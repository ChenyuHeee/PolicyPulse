from ..models import SourceDefinition

SOURCE = SourceDefinition(
    id="imf_worldbank_oecd",
    name="IMF / World Bank / OECD Data",
    type="api",
    homepage="https://www.imf.org/",
    notes="Macro datasets via SDMX or REST endpoints.",
)
