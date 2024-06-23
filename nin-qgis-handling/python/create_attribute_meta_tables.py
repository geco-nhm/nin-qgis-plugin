'''Create meta tables required to create layer attribute tables'''

import json
import tomllib
from pathlib import Path
import pandas as pd

with open(
    file=Path(__file__).parents[1] / 'config.toml',
    mode="rb",
    encoding="utf-8",
) as config_file:
    config = tomllib.load(config_file)

CSV_SAVE_PATH = Path(config['csv_save_paths']['layer_fields_meta'])
ATTRIBUTE_META_PATH = Path(__file__).parents[1] / 'attribute_meta.json'


def main() -> None:
    '''Run script'''

    with open(ATTRIBUTE_META_PATH, mode='r', encoding='utf-8') as json_file:
        attributes: dict = json.load(json_file)

    for attribute_name, attribute_meta in attributes.items():

        attribute_df = pd.DataFrame(
            columns=['name', 'type', 'length', 'precision']
        )

        for idx, (field_name, field_meta) in enumerate(attribute_meta['fields'].items()):

            attribute_df.loc[idx, 'name'] = field_name
            attribute_df.loc[idx, 'type'] = field_meta['dtype']
            attribute_df.loc[idx, 'length'] = field_meta['length']
            attribute_df.loc[idx, 'precision'] = field_meta['precision']

        # Save to csv
        attribute_df.to_csv(
            CSV_SAVE_PATH / f"{attribute_name}_meta.csv",
            encoding='utf-8',
            index=False,
        )


if __name__ == "__main__":
    main()
