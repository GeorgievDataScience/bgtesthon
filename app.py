from pathlib import Path
import random

import pandas as pd
import streamlit as st

from projection_service import build_projection_data

st.set_page_config(page_title="Monthly Rent", layout="centered")
st.title("🏠 Explore Rent Scenarios")

MAX_RENT = 1_000_000
st.session_state.setdefault("rent", "")

TOTAL_RENT_INSIGHT_HORIZONS = [1, 2, 3, 5, 10, 15, 20, 30]
TOTAL_RENT_INSIGHT_LABELS = [f"{y}Y" for y in TOTAL_RENT_INSIGHT_HORIZONS]

RENT_OVER_TIME_SNAPSHOT_LABELS = ["1Y", "2Y", "3Y", "5Y", "10Y", "15Y", "20Y", "30Y"]

_EDITED_NATIVE_COMPARISON_COLS = ("comparison", "comparison02", "comparison03")


def fmt(n: int | float) -> str:
    return f"{n:,.0f}".replace(",", " ")



def load_explanation_text(name: str) -> str:
    path = Path("texts") / name
    return path.read_text(encoding="utf-8")


def load_conclusion_text_by_stat_key(stat_key: str) -> str:
    """Loads conclusion text file by statistic key."""
    filename = f"{stat_key}.txt"
    path = Path("texts") / filename
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip()


@st.cache_data
def load_rent_range_mapping_en() -> pd.DataFrame:
    path = Path("data") / "rent_range_mapping_en.csv"
    last_err: UnicodeDecodeError | None = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "cp1250", "latin-1"):
        try:
            df = pd.read_csv(path, sep=";", encoding=enc)
            break
        except UnicodeDecodeError as e:
            last_err = e
    else:
        raise last_err  # pragma: no cover
    df = df.rename(
        columns={
            df.columns[0]: "from",
            df.columns[1]: "to",
            df.columns[2]: "template",
        }
    )
    return df


@st.cache_data
def load_edited_table_native() -> pd.DataFrame:
    path = Path("data") / "edited_table_native.csv"
    last_err: UnicodeDecodeError | None = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "cp1250", "latin-1"):
        try:
            return pd.read_csv(path, sep=";", encoding=enc)
        except UnicodeDecodeError as e:
            last_err = e
    raise last_err  # pragma: no cover


def _find_edited_native_row(mapping: pd.DataFrame, amount: int) -> pd.Series | None:
    """amount = abs(месечна разлика); инкл. граници, последният ред може да няма to."""
    for _, row in mapping.iterrows():
        lo_i = int(row["from"])
        hi = row["to"]
        if pd.isna(hi) or (isinstance(hi, str) and str(hi).strip() == ""):
            if amount >= lo_i:
                return row
            continue
        hi_i = int(float(hi))
        if lo_i <= amount <= hi_i:
            return row
    return None


def pick_native_table_sentence(mapping: pd.DataFrame, amount_abs: int) -> str:
    """Пълен текст от случайна от трите comparison колони (edited_table_native)."""
    row_match = _find_edited_native_row(mapping, amount_abs)
    if row_match is None:
        return ""
    comp_col = random.choice(_EDITED_NATIVE_COMPARISON_COLS)
    comp_raw = row_match[comp_col]
    if pd.isna(comp_raw):
        return ""
    comp = str(comp_raw).strip()
    if not comp or comp.lower() == "nan":
        return ""
    return comp


def pick_rent_spending_template(mapping: pd.DataFrame, amount: int) -> str:
    """Избира ред от mapping според Total Spending (инкл. граници)."""
    for _, row in mapping.iterrows():
        lo_i = int(row["from"])
        hi = row["to"]
        if pd.isna(hi) or (isinstance(hi, str) and str(hi).strip() == ""):
            if amount >= lo_i:
                return str(row["template"])
            continue
        hi_i = int(float(hi))
        if lo_i <= amount <= hi_i:
            return str(row["template"])
    return ""


def total_spending_for_horizon_years(projection_data: dict, n_years: int) -> int:
    chart_df = projection_data["chart_df"]
    return int(
        chart_df.loc[chart_df["Year"] == n_years - 1, "Total Spending"].iloc[0]
    )


def percent_increase_vs_today(growth_rate: float, years: int) -> float:
    """Процентна промяна спрямо днес: (1 + r)^n - 1, в процентни пунктове."""
    return ((1 + growth_rate) ** years - 1) * 100


def rent_after_years_snapshot_df(
    growth_rate: float, rent_value: float, years: int
) -> pd.DataFrame:
    """Едноколонна таблица (DataFrame): After N year(s); изречения от edited_table_native за месец и година."""
    monthly_at_horizon = int(round(rent_value * (1 + growth_rate) ** years))
    row_will_be = f"Your rent will be {fmt(monthly_at_horizon)} per month"
    pct = percent_increase_vs_today(growth_rate, years)
    factor = (1 + growth_rate) ** years - 1
    monthly_delta = int(round(rent_value * factor))
    yearly_delta = monthly_delta * 12
    col = f"After {years} year" if years == 1 else f"After {years} years"
    pct_r2 = round(pct, 2)
    if factor >= 0:
        row_pct = f"{pct_r2:.2f}% higher"
        row_amt = f"+{fmt(monthly_delta)} more per month"
        row_year = f"That adds up to +{fmt(yearly_delta)} per year"
    else:
        row_pct = f"{abs(pct_r2):.2f}% lower"
        row_amt = f"-{fmt(abs(monthly_delta))} less per month"
        row_year = f"That adds up to {fmt(yearly_delta)} per year"
    mapping_native = load_edited_table_native()
    native_sentence = pick_native_table_sentence(
        mapping_native, abs(monthly_delta)
    )
    native_sentence_year = pick_native_table_sentence(
        mapping_native, abs(yearly_delta)
    )
    return pd.DataFrame(
        {
            col: [
                row_will_be,
                row_pct,
                "",
                row_amt,
                native_sentence,
                "",
                row_year,
                native_sentence_year,
                "",
            ]
        }
    )


def render_rent_projection_summary(projection_data: dict) -> None:
    """Едноколонна рекапитулация под таблицата Explanation (след Start)."""
    initial = fmt(projection_data["rent_value"])
    scenario = projection_data.get("scenario", "—")
    level = projection_data.get("level", projection_data.get("indicator_label", "—"))
    annual = projection_data["growth_rate"]
    rows = [
        f"Initial Rent: {initial}",
        f"Scenario: {scenario}",
        f"Level: {level}",
        f"Annual Change: {annual:.2%}",
        "This means rent doesn’t just grow steadily—it grows faster over time as each increase builds on the last.",
    ]
    summary = pd.DataFrame(rows, columns=["Summary"])
    st.dataframe(summary, hide_index=True, width="stretch")



def render_projection(projection_data: dict):
    st.success(f"💰 Your monthly rent is: {fmt(projection_data['rent_value'])}")
    render_rent_projection_summary(projection_data)
    st.subheader("🏠 Rent Over Time")
    st.caption("👉 How your rent changes year by year")
    view_mode = st.radio(
        "",
        ["📋 Only Table", "📊 Only Chart", "📋📊 Table and Chart"],
        horizontal=True,
        key="projection_view_mode",
        label_visibility="collapsed",
    )

    # Таблица: Your rent today and in the future
    if view_mode in ["📋 Only Table", "📋📊 Table and Chart"]:
        summary_df_display = projection_data["summary_df"].copy()
        # Без pandas Styler (Styler генерира допълнителен HTML слой).
        # Форматираме числата като текст за показване.
        summary_df_display["Monthly Rent"] = summary_df_display[
            "Monthly Rent"
        ].apply(fmt)
        summary_df_display["Annual Rent"] = summary_df_display[
            "Annual Rent"
        ].apply(fmt)
        st.dataframe(summary_df_display, width="stretch", hide_index=True)

        st.caption("Pick a year to see how your rent changes")
        rent_snap_pick = st.segmented_control(
            "Rent over time snapshot",
            RENT_OVER_TIME_SNAPSHOT_LABELS,
            default=RENT_OVER_TIME_SNAPSHOT_LABELS[0],
            key="rent_over_time_snapshot_years",
            label_visibility="collapsed",
        )
        if rent_snap_pick:
            y_snap = int(rent_snap_pick.rstrip("Y"))
            snap_df = rent_after_years_snapshot_df(
                projection_data["growth_rate"],
                float(projection_data["rent_value"]),
                y_snap,
            )
            snap_col = snap_df.columns[0]
            st.dataframe(
                snap_df,
                column_config={
                    snap_col: st.column_config.TextColumn(str(snap_col)),
                },
                width="stretch",
                hide_index=True,
            )

    # Bar chart based on "Your rent today and in the future"
    summary_df = projection_data["summary_df"].copy()
    bar_labels = [
        "current year",
        "after 1 year",
        "after 2 years",
        "after 3 years",
        "after 5 years",
        "after 10 years",
        "after 15 years",
        "after 20 years",
        "after 30 years",
    ]
    summary_df["Bar Label"] = bar_labels[: len(summary_df)]
    # Подреждаме баровете по фиксирания ред на етикетите
    summary_df["Bar Label"] = pd.Categorical(
        summary_df["Bar Label"], categories=bar_labels, ordered=True
    )
    bar_df = summary_df.sort_values("Bar Label").set_index("Bar Label")[
        ["Monthly Rent"]
    ]
    if view_mode in ["📊 Only Chart", "📋📊 Table and Chart"]:
        st.bar_chart(bar_df)

    # Още малко въздух преди Total cost
    st.markdown("")

    st.subheader("💸 Total Rent Paid")
    st.caption("👉 How much you pay in total over time")
    total_view_mode = st.radio(
        "",
        ["📋 Only Table", "📊 Only Chart", "📋📊 Table and Chart"],
        horizontal=True,
        key="total_view_mode",
        label_visibility="collapsed",
    )
    # Таблица за тотал разхода
    if total_view_mode in ["📋 Only Table", "📋📊 Table and Chart"]:
        total_spending_display = projection_data["total_spending_df"].copy()
        # Без pandas Styler (Styler генерира допълнителен HTML слой).
        total_spending_display["Total Spending"] = total_spending_display[
            "Total Spending"
        ].apply(fmt)
        st.dataframe(total_spending_display, width="stretch", hide_index=True)
    # Bar chart за тотал разхода
    total_labels = [
        "In 1 year",
        "In 2 years",
        "In 3 years",
        "In 5 years",
        "In 10 years",
        "In 15 years",
        "In 20 years",
        "In 30 years",
    ]
    total_df = projection_data["total_spending_df"].copy()
    total_df["Bar Label"] = total_labels[: len(total_df)]
    total_df["Bar Label"] = pd.Categorical(
        total_df["Bar Label"], categories=total_labels, ordered=True
    )
    total_bar_df = (
        total_df.sort_values("Bar Label")
        .set_index("Bar Label")[["Total Spending"]]
    )
    if total_view_mode in ["📊 Only Chart", "📋📊 Table and Chart"]:
        st.bar_chart(total_bar_df)

    mapping_native = load_edited_table_native()
    st.caption("Pick a year to see what your rent turns into")
    horizon_pick = st.segmented_control(
        "Spending insight",
        TOTAL_RENT_INSIGHT_LABELS,
        default=TOTAL_RENT_INSIGHT_LABELS[0],
        key="total_rent_paid_insight_horizon",
        label_visibility="collapsed",
    )

    insight_text = ""
    if horizon_pick:
        y = int(horizon_pick.rstrip("Y"))
        spent = total_spending_for_horizon_years(projection_data, y)
        insight_text = pick_native_table_sentence(mapping_native, abs(spent))

    if insight_text:
        st.write(insight_text)

    # Единствен разделител – отделя табличните блокове от обобщаващата графика
    st.divider()

    st.subheader("📊 Rent Trend")
    st.caption("👉 How rent grows over time, shown as a curve")
    _d = chr(36)
    _legacy_projection_metrics = {
        f"Monthly Rent ({_d})": "Monthly Rent",
        f"Annual Rent ({_d})": "Annual Rent",
        f"Total Spending ({_d})": "Total Rent Paid",
    }
    _pcm = st.session_state.get("projection_chart_metric")
    if _pcm in _legacy_projection_metrics:
        st.session_state["projection_chart_metric"] = _legacy_projection_metrics[
            _pcm
        ]
    metric = st.radio(
        "",
        ["Monthly Rent", "Annual Rent", "Total Rent Paid"],
        horizontal=True,
        key="projection_chart_metric",
        label_visibility="collapsed",
    )
    chart_col = "Total Spending" if metric == "Total Rent Paid" else metric
    chart_df = projection_data["chart_df"].set_index("Year")
    st.line_chart(chart_df[[chart_col]])

    st.subheader("Conclusion")
    st.caption("👉 How realistic is this scenario")
    conclusion_text = load_conclusion_text_by_stat_key(
        str(projection_data.get("stat_key", ""))
    )
    if conclusion_text:
        st.write(conclusion_text)


st.caption("Enter your monthly rent and press ▶️ Start")

rent_text = st.text_input(
    "💵 Monthly rent",
    value=st.session_state["rent"],
    placeholder="e.g. 1200",
)
st.session_state["rent"] = rent_text

rent_value = None
error = None

if rent_text:
    try:
        clean = rent_text.replace(" ", "").replace(",", "")
        rent_value = int(clean)

        if rent_value < 0:
            error = "❗ Rent must be positive"
        elif rent_value > MAX_RENT:
            error = (
                "❗ Rent must be below 1,000,000. "
                "If you're a millionaire, this app probably isn’t for you 😄"
            )
    except ValueError:
        error = "❗ Please enter a valid number"


scenario = st.radio(
    "Choose scenario",
    ["🟢 Optimistic", "🔵 Typical", "🔴 Pessimistic", "⚫ Extremes"],
    horizontal=True,
    key="adv_scenario",
)

if scenario == "🟢 Optimistic":
    level = st.radio("Choose scenario level", ["Very Low", "Low"], horizontal=True, key="adv_level_opt")
elif scenario == "🔵 Typical":
    level = st.radio(
        "Choose scenario level", ["Typical", "Average"], horizontal=True, key="adv_level_typ"
    )
elif scenario == "🔴 Pessimistic":
    level = st.radio(
        "Choose scenario level", ["High", "Very High"], horizontal=True, key="adv_level_pess"
    )
else:  # "⚫ Extremes"
    level = st.radio(
        "Choose scenario level", ["Min", "Max"], horizontal=True, key="adv_level_ext"
    )

stat_map = {
    "Very Low": "p10",
    "Low": "p25",
    "Typical": "median",
    "Average": "mean",
    "High": "p75",
    "Very High": "p90",
    "Min": "min",
    "Max": "max",
}

if st.button("▶️ Start", type="primary", key="advanced_start"):
    if error:
        st.error(error)
    elif rent_value is None:
        st.error("❗ Please enter your rent")
    else:
        data = build_projection_data(
            selected_stat_key=stat_map[level],
            indicator_label=level,
            rent_value=rent_value,
        )
        data["stat_key"] = stat_map[level]
        data["scenario"] = scenario
        data["level"] = level
        st.session_state["projection_data"] = data

if "projection_data" in st.session_state and not error:
    render_projection(st.session_state["projection_data"])


with st.expander("How These Scenarios Are Built"):
    st.text(load_explanation_text("rent_model_explanation.txt"))