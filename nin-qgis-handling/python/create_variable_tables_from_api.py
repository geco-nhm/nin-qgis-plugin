#!/usr/bin/env python3
'''Test script for making requests to the NiN API'''

from pathlib import Path
import requests
import tomllib
from tqdm import tqdm  # Progress bar
import pandas as pd

from helpers import sort_mixed_list

# Load config
with open(
    file=Path(__file__).parents[1] / 'config.toml',
    mode="rb",
) as config_file:
    config = tomllib.load(config_file)

# The URLs for the GET requests
NIN_API_BASE_URL = config['api_urls']['base']
VARIABLER_ALLEKODER_URL = f"{NIN_API_BASE_URL}{config['api_urls']['variabler_alle_koder']}"
TYPER_ALLEKODER_URL = f"{NIN_API_BASE_URL}{config['api_urls']['typer_alle_koder']}"
KODEFORHOVEDTYPE_URL = f"{NIN_API_BASE_URL}{config['api_urls']['kode_for_hovedtype']}"
KODEFORGRUNNTYPE_URL = f"{NIN_API_BASE_URL}{config['api_urls']['kode_for_grunntype']}"

# For debugging
CREATE_OVERVIEW = False
CREATE_TYPER = True
# Print results for testing?
VERBOSE = True

# Output csv files save path
CSV_SAVE_PATH = Path(config['csv_save_paths']['attribute_tables']).resolve()


if CREATE_OVERVIEW:
    # GET request for alle koder
    var_allekoder_response = requests.get(VARIABLER_ALLEKODER_URL)

    # Checking if the request was successful
    if var_allekoder_response.status_code == 200:

        # Displaying the response's content as a Python dictionary
        # Note: This assumes that the response is in JSON format
        alle_koder_data = var_allekoder_response.json()

        dataframes = {
            "all_variables": pd.DataFrame(columns=['fid', 'navn', 'kode_id']),
            "variable_trinn": pd.DataFrame(columns=['fid', 'var_fkey', 'maaleskala', 'verdier']),
        }

        var_idx = 0
        trinn_idx = 0

        for variable_category in alle_koder_data['variabler']:

            if VERBOSE:
                print(variable_category['navn'])

            for var in variable_category['variabelnavn']:

                dataframes['all_variables'].loc[var_idx, 'fid'] = var_idx
                dataframes['all_variables'].loc[var_idx, 'navn'] = var['navn']
                dataframes['all_variables'].loc[var_idx,
                                                'kode_id'] = var['kode']['id']

                for maaleskala in var['variabeltrinn']:

                    dataframes['variable_trinn'].loc[trinn_idx,
                                                     'fid'] = trinn_idx
                    dataframes['variable_trinn'].loc[trinn_idx,
                                                     'var_fkey'] = var['kode']['id']
                    dataframes['variable_trinn'].loc[trinn_idx,
                                                     'maaleskala'] = maaleskala['maaleskalaNavn']

                    # List comprehension to store all sorted possible values (verdier) in a string
                    dataframes['variable_trinn'].loc[trinn_idx, 'verdier'] = \
                        ",".join(
                            sort_mixed_list([str(x['verdi'])
                                            for x in maaleskala['trinn']])
                    )

                    trinn_idx += 1

                var_idx += 1

        for df_name, df in dataframes.items():
            df.to_csv(
                CSV_SAVE_PATH / f'{df_name}_attribute_table.csv',
                index=False,
                encoding='utf8',
            )


if CREATE_TYPER:

    # GET request for alle koder
    typer_allekoder_response = requests.get(
        TYPER_ALLEKODER_URL
    )

    # Checking if the request was successful
    if typer_allekoder_response.status_code == 200:
        # Displaying the response's content as a Python dictionary
        # Note: This assumes that the response is in JSON format
        data = typer_allekoder_response.json()

        # Initialize DataFrames
        dataframes = {
            "var_grunntyper": pd.DataFrame(
                columns=['fid', 'grunntype_or_kle_fkey', 'var_name',
                         'var_kode_id', 'maaleskala', 'values', 'display_str'],
            ),
            # "var_M005": pd.DataFrame(columns=['fid', 'hovedtyper_fkey', 'langkode', 'kode_id', 'navn']),
            # "var_M020": pd.DataFrame(columns=['fid', 'hovedtyper_fkey', 'langkode', 'kode_id', 'navn']),
            # "var_M050": pd.DataFrame(columns=['fid', 'hovedtyper_fkey', 'langkode', 'kode_id', 'navn']),
        }

        grunntyper_df = pd.read_csv(
            CSV_SAVE_PATH / "grunntyper_attribute_table.csv",
            index_col=False,
            encoding='utf-8',
        )

        grunntyp_idx = 0
        var_idx = 0

        count = 1
        # 'Typer' level
        for current_type in tqdm(
            data['typer'],
            desc=f"Processing type {count} of {len(data['typer'])}"
        ):
            count += 1

            # 'Hovedtypegrupper' level
            for hovedtypegruppe in current_type['hovedtypegrupper']:

                # 'Hovedtyper' level
                for hovedtyp in hovedtypegruppe['hovedtyper']:

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

                            # Grunntype API request
                            kodeforgrunntype_response = requests.get(
                                KODEFORGRUNNTYPE_URL + grunntyp['kode']['id']
                            )

                            # Checking if the request was successful
                            if kodeforgrunntype_response.status_code == 200:

                                # JSON data to dict
                                kodeforgrunntype_data = \
                                    kodeforgrunntype_response.json()

                                # MO-VU: T1c(0,1,2), T1b(2,3) ; MO-VL: D1b(2,3)

                                for variable_trinn in kodeforgrunntype_data['variabeltrinn']:

                                    # print(variable_trinn)

                                    # Some could be empty (bug in API)
                                    if variable_trinn and variable_trinn['variabelnavn']:

                                        dataframes['var_grunntyper'].loc[
                                            var_idx, 'fid'
                                        ] = var_idx

                                        # GET FKEY FROM EXISTING GRUNNTYPER TABLE
                                        fkey = grunntyper_df.loc[
                                            grunntyper_df['kode_id'] == grunntyp['kode']['id'],
                                            'fid'
                                        ].squeeze()
                                        dataframes['var_grunntyper'].loc[
                                            var_idx, 'grunntype_or_kle_fkey'
                                        ] = fkey

                                        # variabelnavn can also be empty (API bug)
                                        # if variable_trinn['variabelnavn']:
                                        # Var print string
                                        cur_var_info = \
                                            f"{variable_trinn['variabelnavn']['navn']} {variable_trinn['variabelnavn']['kode']['id']}: "
                                        # Other cols
                                        dataframes['var_grunntyper'].loc[
                                            var_idx, 'var_name'
                                        ] = variable_trinn['variabelnavn']['navn']
                                        dataframes['var_grunntyper'].loc[
                                            var_idx, 'var_kode_id'
                                        ] = variable_trinn['variabelnavn']['kode']['id']
                                        # else:
                                        #    cur_var_info = "MISSING NAME: "

                                        # maaleskala_info = []
                                        cur_maaleskala_info = ""

                                        # Add name of maaleskala and realized verdier
                                        # for maaleskala in variable_trinn['maaleskala']:

                                        # ['fid', 'grunntype_or_kle_fkey', 'var_name', 'var_kode_id', 'maaleskala', 'values', 'display_str'],
                                        # Maaleskala and values display string
                                        cur_var_values = ",".join(
                                            sort_mixed_list(
                                                x['verdi'] for x in variable_trinn['maaleskala']['trinn'] if x['registert']
                                            )
                                        )
                                        cur_maaleskala_info += f"{variable_trinn['maaleskala']['maaleskalaNavn']}({cur_var_values})"

                                        # Add to dataframe
                                        dataframes['var_grunntyper'].loc[
                                            var_idx, 'maaleskala'
                                        ] = variable_trinn['maaleskala']['maaleskalaNavn']
                                        dataframes['var_grunntyper'].loc[
                                            var_idx, 'values'
                                        ] = cur_var_values
                                        dataframes['var_grunntyper'].loc[
                                            var_idx, 'display_str'
                                        ] = cur_var_info + cur_maaleskala_info

                                        var_idx += 1

                            else:
                                print(
                                    f'Failed to retrieve data: {kodeforgrunntype_response.status_code}'
                                )

                            grunntyp_idx += 1

                        # TODO: 'Kartleggingsenheter' level

                    else:
                        # Something went wrong
                        print(
                            f'Failed to retrieve data: {kodeforhovedtype_response.status_code}'
                        )

        # Save DataFrames to csv tables
        for df_name, df in dataframes.items():
            df.to_csv(
                CSV_SAVE_PATH / f'{df_name}_attribute_table.csv',
                index=False,
                encoding='utf8',
            )

    else:
        # Something went wrong
        print(f'Failed to retrieve data: {var_allekoder_response.status_code}')
