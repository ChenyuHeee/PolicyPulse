from ..models import SourceDefinition

SOURCE = SourceDefinition(
    id="eia",
    name="U.S. Energy Information Administration (EIA)",
    type="api",
    homepage="https://www.eia.gov/",
    notes="Oil inventory, production, and energy prices.",
    requires={"EIA_API_KEY": "EIA API key"},
)
