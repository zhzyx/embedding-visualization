import os
import pandas as pd

def load_csv(path):
    df = pd.read_csv(path)
    if 'image_path' in df:
        path_0 = df['image_path'].iloc[0]
        if os.path.relpath(path_0) != path_0:
            df['image_path'] = df['image_path'].astype(str).apply(os.path.relpath)
            df.to_csv(path, index=False)
    if 'tsne_x' not in df or 'tsne_y' not in df:
        raise ValueError(f"column 'tsne_x', 'tsn_y' not found in the file")
    return df
