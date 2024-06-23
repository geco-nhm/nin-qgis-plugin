"""
This script is a quick fix to add nature types belonging
into the hovedtypegruppe 'NA-F Limniske vannmassesystemer'
to the attribute tables of coarser mapping units. They will
always be mapped as "grunntyper".
"""

from pathlib import Path
import tomllib
import pandas as pd

with open(
    file=Path(__file__).parents[1] / 'config.toml',
    mode="rb",
    encoding="utf-8",
) as config_file:
    config = tomllib.load(config_file)

CSV_ROOT_PATH = Path(config['csv_save_paths']['attribute_tables'])
LIMNIC_KODE_ID = "NA-F"


def main() -> None:
    """Run as standalone script."""

    # Load tables into dataframes
    dfs_to_load = (
        "hovedtypegrupper", "hovedtyper", "grunntyper",
        "M005", "M020", "M050"
    )
    dfs = {
        df_name: pd.read_csv(
            CSV_ROOT_PATH / f'{df_name}_attribute_table.csv',
            index_col=False,
            encoding='utf-8',
        ) for df_name in dfs_to_load
    }

    # Subset limniske vannmassesystemer
    hovedtypegruppe_fkey = dfs['hovedtypegrupper']['fid'].loc[
        dfs['hovedtypegrupper']['kode_id'] == LIMNIC_KODE_ID
    ].values[0]
    hovedtyper_fkeys = dfs['hovedtyper']['fid'].loc[
        dfs['hovedtyper']['hovedtypegrupper_fkey'] == hovedtypegruppe_fkey
    ].values
    limnic_grunntyper = dfs['grunntyper'].loc[
        dfs['grunntyper']['hovedtyper_fkey'].isin(hovedtyper_fkeys)
    ]

    # Now add info to KLE dataframes
    kartleggingsenheter = ["M005", "M020", "M050"]

    for _, row in limnic_grunntyper.iterrows():
        for kle in kartleggingsenheter:

            # fid,hovedtyper_fkey,langkode,kode_id,navn
            cur_idx = dfs[kle].shape[0]

            # Old kode id example: FM05-01
            # Updated kode id example: FM05-M005-01
            old_kode_id = str(row['kode_id'])
            updated_kode_id = old_kode_id.split("-")
            updated_kode_id.insert(1, f"-{kle}-")
            updated_kode_id = "".join(updated_kode_id)

            # Also update in display string
            updated_navn = row['navn'].split(" ")
            updated_navn[0] = updated_kode_id
            updated_navn = " ".join(updated_navn)

            # Copy grunntype entries to KLE dataframes
            dfs[kle].loc[cur_idx, 'fid'] = cur_idx
            dfs[kle].loc[cur_idx, 'hovedtyper_fkey'] = \
                row['hovedtyper_fkey']
            dfs[kle].loc[cur_idx, 'langkode'] = \
                row['langkode']
            dfs[kle].loc[cur_idx, 'kode_id'] = \
                updated_kode_id
            dfs[kle].loc[cur_idx, 'navn'] = \
                updated_navn

            # NOW ADD TO GRUNNTYPE ENTRY
            dfs['grunntyper'].loc[
                dfs['grunntyper']['kode_id'] == old_kode_id,
                f"kartleggingsenhet_{kle.lower()}_fkey"
            ] = updated_kode_id

    # print(dfs[kle].convert_dtypes().dtypes)

    for dfs_to_save in (["grunntyper"] + kartleggingsenheter):
        dfs[dfs_to_save].convert_dtypes().to_csv(
            CSV_ROOT_PATH / 'limniske_quickfix' /
            f'{dfs_to_save}_attribute_table.csv',
            index=False,
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
