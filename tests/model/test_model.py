import pandas as pd
import pytest

DEFAULT_TECHNOLOGIES = set([
    "battery", "hydrogen", "open_field_pv", "wind_onshore_competing", "wind_onshore_monopoly",
    "roof_mounted_pv", "wind_offshore", "hydro_run_of_river", "hydro_reservoir", "pumped_hydro",
    "biofuel", "demand_elec"
])
DIRECTIONAL_PV = set(["roof_mounted_pv_s_flat", "roof_mounted_pv_n", "roof_mounted_pv_e_w"])

TECHNOLOGIES = {
    "default": DEFAULT_TECHNOLOGIES,
    "connected": DEFAULT_TECHNOLOGIES,
    "directional-pv": (DEFAULT_TECHNOLOGIES | DIRECTIONAL_PV) - set(["roof_mounted_pv"]),
    "frozen-hydro": DEFAULT_TECHNOLOGIES,
    "alternative-cost": DEFAULT_TECHNOLOGIES,
    "shed-load": DEFAULT_TECHNOLOGIES | set(["load_shedding"]),
}


@pytest.fixture(scope="function")
def technologies(scenario):
    return TECHNOLOGIES[scenario]


def test_model_runs(optimised_model):
    assert optimised_model.results.termination_condition == "optimal"


def test_example_model_runs(optimised_example_model):
    assert optimised_example_model.results.termination_condition == "optimal"


def test_technologies_are_available(energy_cap, location, technologies):
    for technology in technologies:
        assert (
            (technology in energy_cap.techs)
            and pd.notna(energy_cap.sel(locs=location, techs=technology).item())
        )
