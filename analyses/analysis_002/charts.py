"""Prepare chart and historical table datasets (no Streamlit side effects)."""

def prepare_index_data(filtered_df):
    chart_data = filtered_df.loc[:, ["year", "idx_value"]].sort_values("year")
    yearly_values = (
        filtered_df.loc[:, ["year", "percentage_change_inx", "idx_value"]]
        .sort_values("year")
        .rename(columns={
            "year": "Година",
            "percentage_change_inx": "Изменение на цените (%)",
            "idx_value": "Индекс на цените",
        })
    )
    return chart_data, yearly_values
