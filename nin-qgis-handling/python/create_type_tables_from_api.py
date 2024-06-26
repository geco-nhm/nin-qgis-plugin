#!/usr/bin/env python3
'''Test script for making requests to the NiN API'''

from pathlib import Path
import requests
import tomllib
import pandas as pd

with open(
    file=Path(__file__).parents[1] / 'config.toml',
    mode="rb",
) as config_file:
    config = tomllib.load(config_file)

# The URLs for the GET requests
NIN_API_BASE_URL = config['api_urls']['base']
ALLEKODER_URL = f'{NIN_API_BASE_URL}{config['api_urls']['typer_alle_koder']}'
KODEFORHOVEDTYPE_URL = f'{NIN_API_BASE_URL}{config['api_urls']['kode_for_hovedtype']}'

# Output csv files save path
CSV_SAVE_PATH = Path(config['csv_save_paths']['attribute_tables']).resolve()

# Print results for testing?
VERBOSE = False

# Optional: headers can be used to provide additional information with your request
# headers = {
#    'Accept': 'application/json',  # Example header: asking for a JSON response
#    'Authorization': 'Bearer your_api_token'  # Example header: bearer token authorization
# }

# GET request for alle koder
allekoder_response = requests.get(ALLEKODER_URL)  # , headers=headers)

# Checking if the request was successful
if allekoder_response.status_code == 200:
    # Displaying the response's content as a Python dictionary
    # Note: This assumes that the response is in JSON format
    data = allekoder_response.json()

    # Initialize DataFrames
    dataframes = {
        "typer": pd.DataFrame(columns=['fid', 'langkode', 'kode_id', 'navn']),
        "hovedtypegrupper": pd.DataFrame(columns=['fid', 'typer_fkey', 'langkode', 'kode_id', 'navn']),
        "hovedtyper": pd.DataFrame(columns=['fid', 'hovedtypegrupper_fkey', 'langkode', 'kode_id', 'navn']),
        "grunntyper": pd.DataFrame(
            columns=[
                'fid', 'hovedtyper_fkey', 'langkode', 'kode_id', 'navn',
                'kartleggingsenhet_m005_fkey', 'kartleggingsenhet_m020_fkey',
                'kartleggingsenhet_m050_fkey'
            ]
        ),
        "M005": pd.DataFrame(columns=['fid', 'hovedtyper_fkey', 'langkode', 'kode_id', 'navn']),
        "M020": pd.DataFrame(columns=['fid', 'hovedtyper_fkey', 'langkode', 'kode_id', 'navn']),
        "M050": pd.DataFrame(columns=['fid', 'hovedtyper_fkey', 'langkode', 'kode_id', 'navn']),
    }

    type_idx = 0
    hovedtypegrupper_idx = 0
    hovedtyp_idx = 0
    grunntyp_idx = 0

    # 'Typer' level
    for current_type in data['typer']:
        if VERBOSE:
            print(f"Current type: {current_type['navn']}")
            print("Hovedtypegrupper and Hovedtyper:")

        dataframes['typer'].loc[type_idx, 'fid'] = type_idx
        dataframes['typer'].loc[type_idx,
                                'langkode'] = current_type['kode']['langkode']
        dataframes['typer'].loc[type_idx,
                                'kode_id'] = current_type['kode']['id']
        dataframes['typer'].loc[type_idx, 'navn'] = \
            f"{current_type['kode']['id']} {current_type['navn']}"

        # 'Hovedtypegrupper' level
        for hovedtypegruppe in current_type['hovedtypegrupper']:
            if VERBOSE:
                print(f"- {hovedtypegruppe['navn']}")

            dataframes['hovedtypegrupper'].loc[
                hovedtypegrupper_idx, 'fid'
            ] = hovedtypegrupper_idx
            dataframes['hovedtypegrupper'].loc[
                hovedtypegrupper_idx, 'typer_fkey'
            ] = type_idx
            dataframes['hovedtypegrupper'].loc[
                hovedtypegrupper_idx, 'langkode'
            ] = hovedtypegruppe['kode']['langkode']
            dataframes['hovedtypegrupper'].loc[
                hovedtypegrupper_idx, 'kode_id'
            ] = hovedtypegruppe['kode']['id']
            dataframes['hovedtypegrupper'].loc[
                hovedtypegrupper_idx, 'navn'
            ] = f"{hovedtypegruppe['kode']['id']} {hovedtypegruppe['navn']}"

            # 'Hovedtyper' level
            for hovedtyp in hovedtypegruppe['hovedtyper']:
                if VERBOSE:
                    print(f"  • {hovedtyp['navn']}")

                dataframes['hovedtyper'].loc[
                    hovedtyp_idx, 'fid'
                ] = hovedtyp_idx
                dataframes['hovedtyper'].loc[
                    hovedtyp_idx, 'hovedtypegrupper_fkey'
                ] = hovedtypegrupper_idx
                dataframes['hovedtyper'].loc[
                    hovedtyp_idx, 'langkode'
                ] = hovedtyp['kode']['langkode']
                dataframes['hovedtyper'].loc[
                    hovedtyp_idx, 'kode_id'
                ] = hovedtyp['kode']['id']
                dataframes['hovedtyper'].loc[
                    hovedtyp_idx, 'navn'
                ] = f"{hovedtyp['kode']['id']} {hovedtyp['navn']}"

                # MAKE NEW API REQUEST FOR CURRENTS HOVEDTYPE'S
                # GRUNNTYPER
                kodeforhovedtype_response = requests.get(
                    KODEFORHOVEDTYPE_URL + hovedtyp['kode']['id']
                )

                # Checking if the request was successful
                if kodeforhovedtype_response.status_code == 200:

                    kodeforhovedtype_data = kodeforhovedtype_response.json()

                    # 'Grunntyper' level
                    for grunntyp in kodeforhovedtype_data['grunntyper']:

                        dataframes['grunntyper'].loc[grunntyp_idx,
                                                     'fid'] = grunntyp_idx
                        dataframes['grunntyper'].loc[grunntyp_idx, 'hovedtyper_fkey'] = \
                            hovedtyp_idx
                        dataframes['grunntyper'].loc[grunntyp_idx, 'langkode'] = \
                            grunntyp['kode']['langkode']
                        dataframes['grunntyper'].loc[grunntyp_idx, 'kode_id'] = \
                            grunntyp['kode']['id']
                        dataframes['grunntyper'].loc[
                            grunntyp_idx, 'navn'
                        ] = f"{grunntyp['kode']['id']} {grunntyp['navn']}"

                        grunntyp_idx += 1

                    # 'Kartleggingsenheter' level
                    for kartleggingsenhet in kodeforhovedtype_data['kartleggingsenheter']:

                        # Names in API request must be the same as in 'kartleggingsenheter_dfs' dict
                        current_mapping_unit = kartleggingsenhet["maalestokkEnum"]
                        cur_enhets_idx = dataframes[current_mapping_unit].shape[0]

                        # Fid
                        dataframes[current_mapping_unit].loc[
                            cur_enhets_idx, "fid"
                        ] = cur_enhets_idx
                        # Hovedtyper fkey
                        dataframes[current_mapping_unit].loc[
                            cur_enhets_idx, 'hovedtyper_fkey'
                        ] = hovedtyp_idx
                        # langkode
                        dataframes[current_mapping_unit].loc[
                            cur_enhets_idx, "langkode"
                        ] = kartleggingsenhet["kode"]["langkode"]
                        # kode_id
                        dataframes[current_mapping_unit].loc[
                            cur_enhets_idx, "kode_id"
                        ] = kartleggingsenhet["kode"]["id"]
                        # navn
                        dataframes[current_mapping_unit].loc[
                            cur_enhets_idx, "navn"
                        ] = f"{kartleggingsenhet['kode']['id']} {kartleggingsenhet['navn']}"

                        # Set kartleggingsenheter IDs as foreign keys in 'grunntyper_df'
                        for grunntyp in kartleggingsenhet['grunntyper']:

                            # Determine grunntyper_df index of current grunntyp
                            cur_idx = dataframes['grunntyper'].index[
                                # Condition
                                dataframes['grunntyper']['kode_id'] == grunntyp['kode']['id']
                            ].tolist()[0]  # List should only contain one element

                            dataframes['grunntyper'].loc[
                                cur_idx,
                                f'kartleggingsenhet_{current_mapping_unit.lower()}_fkey'
                            ] = kartleggingsenhet["kode"]["id"]

                else:
                    # Something went wrong
                    print(
                        f'Failed to retrieve data: {kodeforhovedtype_response.status_code}'
                    )

                hovedtyp_idx += 1

            hovedtypegrupper_idx += 1

        type_idx += 1

        if VERBOSE:
            print("-"*15+"\n")


    # Save DataFrames to csv tables
    for df_name, df in dataframes.items():
        df.to_csv(
            CSV_SAVE_PATH / f'{df_name}_attribute_table.csv',
            index=False,
            encoding='utf8',
        )

else:
    # Something went wrong
    print(f'Failed to retrieve data: {allekoder_response.status_code}')
