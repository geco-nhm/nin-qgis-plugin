'''
Infers the variables that distinguish kartleggingsenheter based on the
aggregated grunntyper variables and saves them in csv tables.
'''

import copy
from pathlib import Path
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

CSV_ROOT_PATH = Path(config['csv_save_paths']['attribute_tables']).resolve()

INCLUDED_KARTLEGGINGSENEHTER = [
    'M005',
    'M020',
    'M050',
]


def main() -> None:
    '''Execute as standalone script'''

    # Read attribute tables
    grunntyper_df = pd.read_csv(
        CSV_ROOT_PATH / 'grunntyper_attribute_table.csv',
        index_col=False,
        encoding='utf-8',
    )
    var_grunntyper_df = pd.read_csv(
        CSV_ROOT_PATH / 'var_grunntyper_attribute_table.csv',
        index_col=False,
        encoding='utf-8',
    )

    # Initialize new variable attribute tables for kartleggingsenheter
    # in a dict
    var_kartleggingsenheter_dfs = {
        kle: pd.DataFrame(
            columns=['fid', 'grunntype_or_kle_fkey', 'var_name',
                     'var_kode_id', 'maaleskala', 'values', 'display_str']
        ) for kle in INCLUDED_KARTLEGGINGSENEHTER
    }

    # Retrieve unique hovedtyper fids
    unique_hovedtyper_fids = sorted(set(grunntyper_df['hovedtyper_fkey']))

    # Loop through different kartleggingsenheter
    for included_kle in INCLUDED_KARTLEGGINGSENEHTER:

        hovedtype_dict = {}

        for hovedtyp_fid in tqdm(
            unique_hovedtyper_fids,
            desc="Processing KLE:"
        ):

            # Subset grunntyper belonging to current hovedtype
            cur_grunntyper_mask = (
                grunntyper_df['hovedtyper_fkey'] == hovedtyp_fid
            )
            cur_grunntyper_df = grunntyper_df.loc[cur_grunntyper_mask]

            try:
                # Unique kartleggingsenhet IDs for current hovedtype, sorted by ID...
                unique_kartleggingsenheter_ids = sorted(set(
                    # ...where entries are not NaN in the API generated table
                    cur_grunntyper_df[f"kartleggingsenhet_{included_kle.lower()}_fkey"].loc[
                        cur_grunntyper_df[f"kartleggingsenhet_{included_kle.lower()}_fkey"].notnull(
                        )
                    ]
                ))
            except Exception as exception:
                print(
                    f"Error when comparing unique kartleggingsenhet_{included_kle.lower()}_fkey!"
                )
                print(
                    cur_grunntyper_df[f"kartleggingsenhet_{included_kle.lower()}_fkey"]
                )
                raise exception

            # Loop through unique kartleggingsenhet IDs in current hovedtype
            # to generate concatenated var lists.
            # Will not be entered if only NaNs found in 'unique_kartleggingsenheter_ids'.

            helper_dict = {}

            for unique_kle_id in unique_kartleggingsenheter_ids:

                helper_dict[unique_kle_id] = {}

                # Loop through fid's of all grunntyper that belong to the current kartleggingsenhet...
                for grunntype_id in grunntyper_df['fid'].loc[
                    grunntyper_df[f"kartleggingsenhet_{included_kle.lower()}_fkey"] == unique_kle_id
                ]:

                    # Subset all rows (different vars) for current KLE's current grunntype
                    cur_kle_vars_df = var_grunntyper_df.loc[
                        var_grunntyper_df['grunntype_or_kle_fkey'] == grunntype_id
                    ]

                    # Loop through rows
                    for _, row in cur_kle_vars_df.iterrows():

                        # Hacky way to construct dataframe later on --> split at |
                        cur_var_name = \
                            f"{row['var_name']}|{row['var_kode_id']}|{row['maaleskala']}"
                        cur_var_vals = str(row['values'])

                        # Current variable already added to kartleggingsenhets dict entry?
                        if cur_var_name in helper_dict[unique_kle_id].keys():
                            # Then add individual elements to existing set
                            helper_dict[unique_kle_id][cur_var_name].update(
                                cur_var_vals.split(",")
                            )
                        else:
                            # First time added? Create a set with individual values
                            # (set gets rid of duplicate entries)
                            helper_dict[unique_kle_id][cur_var_name] = set()
                            helper_dict[unique_kle_id][cur_var_name].update(
                                cur_var_vals.split(",")
                            )

                # If no variable info was given via API, delete again
                if not helper_dict[unique_kle_id]:
                    del helper_dict[unique_kle_id]

            if helper_dict:

                # After collecting all variables for all KLEs in a hovedtype
                # (if there are any), we remove vars that have identical values
                # across *all* KLEs

                union_all_vars_in_hovedtype = {}

                # print(f"Before merge:\n{helper_dict}")

                # Loop through each kartleggingsenhet
                for kle, _ in helper_dict.items():
                    # Loop through each variable in the kartleggingsenhet
                    for variable, value in helper_dict[kle].items():
                        # If the variable is not already in the dictionary, create a new set for it
                        if variable not in union_all_vars_in_hovedtype:
                            union_all_vars_in_hovedtype[variable] = set()
                        # Add the value for the variable from this kartleggingsenhet to the set
                        union_all_vars_in_hovedtype[variable].update(value)

                # print(f"Union all vars hovedtype:\n{union_all_vars_in_hovedtype}")

                # Now we can identify variables where all kartleggingsenheter have the same value
                var_difference_counts = {
                    key: 0 for key in union_all_vars_in_hovedtype  # Loop through dict keys
                }
                # print(f"var difference counts:\n{var_difference_counts}")
                for kle, var_dict in helper_dict.items():
                    for var, kle_values in var_dict.items():
                        if not kle_values == union_all_vars_in_hovedtype[var]:
                            var_difference_counts[var] += 1
                # print(f"var difference counts:\n{var_difference_counts}")

                identical_variables = [
                    var for var, count in var_difference_counts.items() if (count == 0)
                ]

                # print(f"Identical variables:\n{identical_variables}")

                # Finally, we exclude the common variables and retain the others
                unique_variables = copy.deepcopy(helper_dict)
                # If length of dict is 1, we need to keep the information
                if len(unique_variables) != 1:
                    # print(helper_dict)
                    for kle, var_dict in helper_dict.items():
                        for var_name, _ in var_dict.items():
                            if var_name in identical_variables:
                                del unique_variables[kle][var_name]

                # print(f"After merge:\n{unique_variables}")

                # Attach fully processed dict to hovedtype_dict
                hovedtype_dict[str(hovedtyp_fid)] = unique_variables

        # print({k: hovedtype_dict[k] for k in list(hovedtype_dict)[:2]})
        # Now we need to create tables from the dict and retrieve the fids
        # for the kartleggingsenheter
        cur_kle_attr_table = pd.read_csv(
            CSV_ROOT_PATH / f"{included_kle}_attribute_table.csv",
            index_col=False,
            encoding='utf-8',
        )

        kle_var_fid = 0
        for _, kle_dict in hovedtype_dict.items():
            for kle_id_kode, kle_var_dict in kle_dict.items():
                # Get fid of current kartleggingsenhet from attribute table
                cur_fkey = cur_kle_attr_table.loc[
                    cur_kle_attr_table['kode_id'] == kle_id_kode,
                    "fid"
                ].values[0]
                for hacky_var_str, var_vals in kle_var_dict.items():
                    # FID
                    var_kartleggingsenheter_dfs[included_kle].loc[
                        kle_var_fid, 'fid'
                    ] = kle_var_fid
                    # FKEY
                    var_kartleggingsenheter_dfs[included_kle].loc[
                        kle_var_fid, 'grunntype_or_kle_fkey'
                    ] = str(cur_fkey)

                    # Now split hacky string
                    hacky_list = hacky_var_str.split("|")

                    # VAR NAME
                    var_kartleggingsenheter_dfs[included_kle].loc[
                        kle_var_fid, 'var_name'
                    ] = hacky_list[0]
                    # VAR KODE
                    var_kartleggingsenheter_dfs[included_kle].loc[
                        kle_var_fid, 'var_kode_id'
                    ] = hacky_list[1]
                    # MAALESKALA
                    var_kartleggingsenheter_dfs[included_kle].loc[
                        kle_var_fid, 'maaleskala'
                    ] = hacky_list[2]

                    # VALUES!
                    concat_var_vals = ",".join(
                        sort_mixed_list([x for x in var_vals])
                    )
                    var_kartleggingsenheter_dfs[included_kle].loc[
                        kle_var_fid, 'values'
                    ] = concat_var_vals

                    # DISPLAY STRING
                    var_kartleggingsenheter_dfs[included_kle].loc[
                        kle_var_fid, 'display_str'
                    ] = f"{hacky_list[0]} {hacky_list[1]}: {hacky_list[2]}({concat_var_vals})"

                    kle_var_fid += 1

    # FINALLY, save all dfs to csv
    for df_name, df in var_kartleggingsenheter_dfs.items():
        df.to_csv(
            CSV_ROOT_PATH / f'var_{df_name}_attribute_table.csv',
            index=False,
            encoding='utf8',
        )


if __name__ == "__main__":
    main()
