from pathlib import Path

import numpy as np
import pandas as pd
from styleframe import StyleFrame

from eurocalliopelib import utils

idx = pd.IndexSlice

DATASET_PARAMS = {
    "road-energy": {
        "sheet_name": "TrRoad_ene",
        "idx_start_str": "Total energy consumption",
        "idx_end_str": "Indicators",
        "unit": "ktoe"
    },
    "road-distance": {
        "sheet_name": "TrRoad_act",
        "idx_start_str": "Vehicle-km driven",
        "idx_end_str": "Stock of vehicles",
        "unit": "mio_km"
    },
    "road-vehicles": {
        "sheet_name": "TrRoad_act",
        "idx_start_str": "Stock of vehicles - in use",
        "idx_end_str": "New vehicle-registrations",
        "unit": "N. vehicles"
    }
}

ROAD_CARRIERS = {
    'Gasoline engine': 'petrol',
    'Diesel oil engine': 'diesel',
    'Natural gas engine': 'natural_gas',
    'LPG engine': 'lpg',
    'Battery electric vehicles': 'electricity',
    'Plug-in hybrid electric': 'petrol'
}


def process_jrc_transport_data(data_dir, dataset, out_path):
    data_filepaths = list(Path(data_dir).glob("*.xlsx"))
    processed_data = pd.concat([
        read_transport_excel(file, **DATASET_PARAMS[dataset])
        for file in data_filepaths
    ])
    print(DATASET_PARAMS[dataset]["unit"])
    if DATASET_PARAMS[dataset]["unit"] == "ktoe":
        processed_data = processed_data.apply(utils.ktoe_to_twh)
        print(processed_data)
        # bei meinem dataset gibt es gar kein unit, in dem bei bryn drinnen gibt es dies, hier wird ez einfach umegrechnet
        # falls dies nötig wird kann ich einf noch hinzufügen, ist ja überall ktoe, dies is allgemein gültig für alle 3
        # datasets, haben alle unit
        #processed_data.index = processed_data.index.set_levels(['twh'], level='unit')



    processed_data.stack('year').to_csv(out_path)

    # EXPLANATION: Here I created the country code mappings code for normal pandas, since i didnt want a dataframe, but
    # shortly after realised that this isnt done in the code provided by the other branch by tim

    #processed_da = processed_data.stack().rename(f"jrc-idees-transport-{dataset}").to_xarray()
    #print(processed_data)
    #country_code_mapping = utils.convert_valid_countries(processed_data.index.get_level_values('country_code').unique().tolist())
    #print(country_code_mapping)
    #processed_data = rename_country_codes(processed_data, country_code_mapping)
    #print(processed_data)
    #processed_da.assign_attrs(unit=unit).to_netcdf()
    #print(processed_da)





def read_transport_excel(file, sheet_name, idx_start_str, idx_end_str, **kwargs):
    xls = pd.ExcelFile(file)
    style_df = StyleFrame.read_excel(xls, read_style=True, sheet_name=sheet_name)
    df = pd.read_excel(xls, sheet_name=sheet_name)
    column_names = str(style_df.data_df.columns[0])
    # We have manually identified the section of data which is of use to us,
    # given by idx_start_str and idx_end_str.
    idx_start = int(style_df[style_df[column_names].str.find(idx_start_str) > -1][0])
    idx_end = int(style_df[style_df[column_names].str.find(idx_end_str) > -1][0])
    df = df.assign(indent=style_df[column_names].style.indent.astype(int)).loc[idx_start:idx_end]

    total_to_check = df.iloc[0]
    # The indent of the strings in the first column of data indicates their hierarchy in a multi-level index.
    # Two levels of the hierarchy are identified here and ffill() is used to match all relevant rows to the top-level name.
    df['section'] = df.where(df.indent == 1).iloc[:, 0].ffill()
    df['vehicle_type'] = df.where(df.indent == 2).iloc[:, 0].ffill()

    if sheet_name == 'TrRoad_act':
        df = process_road_vehicles(df, column_names)
    elif sheet_name == 'TrRoad_ene':
        df = process_road_energy(df, column_names)
    df = (
        df
        .assign(country_code=column_names.split(' - ')[0])
        .set_index('country_code', append=True)
    )
    df.columns = df.columns.astype(int).rename('year')

    # After all this hardcoded cleanup, make sure numbers match up
    assert np.allclose(
        df.sum(),
        total_to_check.loc[df.columns].astype(float)
    )

    return df


def process_road_vehicles(df, column_names):
    # The indent of the strings in the first column of data indicates their hierarchy in a multi-level index.
    # The vehicle subtype is identified here and ffill() is used to match all relevant rows to this subtype.
    df['vehicle_subtype'] = df.where(df.indent == 3).iloc[:, 0]
    # ASSUME: 2-wheelers are powered by fuel oil.
    # All useful information is either when the index column string is indented 3 times,
    # or when the vehicle type is a 2-wheeler. One of the many ways in which this dataset is a pain.
    df = df.where(
        (df.indent == 3) | (df.vehicle_type == 'Powered 2-wheelers')
    ).dropna(how='all')
    df.loc[df.vehicle_type == 'Powered 2-wheelers', 'vehicle_subtype'] = 'Gasoline engine'
    return (
        df
        .set_index(['section', 'vehicle_type', 'vehicle_subtype'])
        .drop([column_names, 'indent'], axis=1)
    )


def process_road_energy(df, column_names):
    # The indent of the strings in the first column of data indicates their hierarchy in a multi-level index.
    # The vehicle subtype is identified here and ffill() is used to match all relevant rows to this subtype.
    df['vehicle_subtype'] = df.where(df.indent == 3).iloc[:, 0].ffill()
    # Remove bracketed information from the vehicle type and subtype
    df['vehicle_type'] = df['vehicle_type'].str.split('(', expand=True)[0].str.strip()
    df['vehicle_subtype'] = df['vehicle_subtype'].str.split('(', expand=True)[0].str.strip()
    # ASSUME: Powered 2-wheelers are gasoline engine only (this is implicit when looking at the Excel sheet directly)
    df.loc[df.vehicle_type == 'Powered 2-wheelers', 'vehicle_subtype'] = 'Gasoline engine'
    df['carrier'] = df.where(df.indent == 4).iloc[:, 0]
    df['carrier'] = df['carrier'].str.replace('of which ', '')
    # Powered 2-wheelers use petrol, some of which is biofuels (we deal with the 'of which' part later)
    df.loc[(df.vehicle_type == 'Powered 2-wheelers') & (df.indent == 2), 'carrier'] = 'petrol'
    df.loc[(df.vehicle_type == 'Powered 2-wheelers') & (df.indent == 3), 'carrier'] = 'biofuels'
    # ASSUME: both domestic and international freight uses diesel (this is implicit when looking at the Excel sheet directly)
    df.loc[(df.vehicle_subtype == 'Domestic') & (df.indent == 3), 'carrier'] = 'diesel'
    df.loc[(df.vehicle_subtype == 'International') & (df.indent == 3), 'carrier'] = 'diesel'
    # All other vehicle types mention the drive-train directly, so we translate that to energy carrier here
    df['carrier'] = df['carrier'].fillna(df.vehicle_subtype.replace(ROAD_CARRIERS))

    df = (
        df
        .where((df.indent > 2) | (df.vehicle_type == 'Powered 2-wheelers'))
        .dropna()
        .set_index(['section', 'vehicle_type', 'vehicle_subtype', 'carrier'])
        .drop([column_names, 'indent'], axis=1)
    )

    df = remove_of_which(df, 'diesel', 'biofuels')
    df = remove_of_which(df, 'petrol', 'biofuels')
    df = remove_of_which(df, 'petrol', 'electricity')
    df = remove_of_which(df, 'natural_gas', 'biogas')

    return df


def remove_of_which(df, main_carrier, of_which_carrier):
    """
    Subfuels (e.g. biodiesel) are given as 'of which ...', meaning the main fuel consumption
    includes those fuels (diesel is actually diesel + biofuels). We rectify that here
    """
    updated_carrier = (
        (df.xs(main_carrier, level='carrier') - df.xs(of_which_carrier, level='carrier'))
        .dropna()
        .assign(carrier=main_carrier)
        .set_index('carrier', append=True)
    )
    df.loc[updated_carrier.index] = updated_carrier
    return df

# code used for case where I rename dataframe
def rename_country_codes(df: pd.DataFrame, rename_dict: dict) -> pd.DataFrame:
    """
    Rename country codes in a DataFrame with MultiIndex.

    Args:
        df (pd.DataFrame): Input DataFrame.
        rename_dict (dict): Mapping from old to new country codes.

    Returns:
        pd.DataFrame: DataFrame with renamed country codes.
    """

    # Get the level number for 'country_code'
    level_number = df.index.names.index('country_code')

    # Create the modified levels
    modified_levels = [
        level.map(rename_dict) if i == level_number else level
        for i, level in enumerate(df.index.levels)
    ]

    # Set the modified levels in the DataFrame
    df.index = df.index.set_levels(modified_levels)

    return df

if __name__ == "__main__":
    process_jrc_transport_data(
        data_dir=snakemake.input.unprocessed_data,
        dataset=snakemake.wildcards.dataset,
        out_path=snakemake.output[0]
    )
