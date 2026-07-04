from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from projection_service import build_projection_data, get_growth_rate_for_stat

PLAUSIBLE_SCRIPT_ID = "plausible-analytics"
PLAUSIBLE_SCRIPT_SRC = "https://plausible.io/js/pa-uhz1-Tp2pq3SUeB5_9qm0.js"


def inject_plausible_analytics() -> None:
    """Inject Plausible into the parent page (Streamlit shell), not the component iframe."""
    components.html(
        f"""
        <script>
        (function () {{
            var doc = parent.document;
            if (doc.getElementById("{PLAUSIBLE_SCRIPT_ID}")) return;
            var s = doc.createElement("script");
            s.id = "{PLAUSIBLE_SCRIPT_ID}";
            s.async = true;
            s.src = "{PLAUSIBLE_SCRIPT_SRC}";
            doc.head.appendChild(s);
            var init = doc.createElement("script");
            init.id = "{PLAUSIBLE_SCRIPT_ID}-init";
            init.textContent = "window.plausible=window.plausible||function(){{(plausible.q=plausible.q||[]).push(arguments)}},plausible.init=plausible.init||function(i){{plausible.o=i||{{}}}};plausible.init()";
            doc.head.appendChild(init);
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


st.set_page_config(page_title="Месечен наем", layout="centered")
inject_plausible_analytics()
st.title("🏠 Разгледай сценарии за наем")

MAX_RENT = 1_000_000
st.session_state.setdefault("rent", "")

TOTAL_RENT_INSIGHT_HORIZONS = [1, 2, 3, 5, 10, 15, 20, 30]
TOTAL_RENT_INSIGHT_LABELS = [f"{y}г" for y in TOTAL_RENT_INSIGHT_HORIZONS]

RENT_OVER_TIME_SNAPSHOT_LABELS = ["1г", "2г", "3г", "5г", "10г", "15г", "20г", "30г"]


def parse_year_label(label: str) -> int:
    return int(label.rstrip("г"))


def fmt(n: int | float) -> str:
    return f"{n:,.0f}".replace(",", " ")


@st.cache_data
def load_spending_ranges() -> pd.DataFrame:
    path = Path("data") / "spending_ranges.csv"
    last_err: UnicodeDecodeError | None = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "cp1250", "latin-1"):
        try:
            return pd.read_csv(path, sep=";", encoding=enc)
        except UnicodeDecodeError as e:
            last_err = e
    raise last_err  # pragma: no cover


def _find_spending_range_row(mapping: pd.DataFrame, amount: int) -> pd.Series | None:
    """Интервал from–to (вкл.); последният ред може да няма to (amount >= from)."""
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


def spending_range_insight(
    mapping: pd.DataFrame, years: int, spent_abs: int
) -> tuple[str, str]:
    """(after_year с подставени years/amount, comparison) от spending_ranges за spent_abs."""
    row_match = _find_spending_range_row(mapping, spent_abs)
    if row_match is None:
        return "", ""
    tpl_raw = row_match.get("after_year", "")
    tpl = "" if pd.isna(tpl_raw) else str(tpl_raw).strip()
    after = (
        tpl.replace("{years}", str(years)).replace("{amount}", fmt(spent_abs))
        if tpl
        else ""
    )
    comp_raw = row_match.get("comparison", "")
    if pd.isna(comp_raw):
        return after, ""
    comp = str(comp_raw).strip()
    if not comp or comp.lower() == "nan":
        return after, ""
    return after, comp


def total_spending_for_horizon_years(projection_data: dict, n_years: int) -> int:
    chart_df = projection_data["chart_df"]
    return int(
        chart_df.loc[chart_df["Година"] == n_years - 1, "Общо платено"].iloc[0]
    )


def percent_increase_vs_today(growth_rate: float, years: int) -> float:
    """Процентна промяна спрямо днес: (1 + r)^n - 1, в процентни пунктове."""
    return ((1 + growth_rate) ** years - 1) * 100


def rent_after_years_snapshot_df(
    growth_rate: float,
    rent_value: float,
    years: int,
) -> pd.DataFrame:
    """Под месечна и годишна разлика само comparison редове от spending_ranges."""
    monthly_at_horizon = int(round(rent_value * (1 + growth_rate) ** years))
    row_will_be = f"Наемът ви ще бъде {fmt(monthly_at_horizon)} на месец"
    pct = percent_increase_vs_today(growth_rate, years)
    factor = (1 + growth_rate) ** years - 1
    monthly_delta = int(round(rent_value * factor))
    yearly_delta = monthly_delta * 12
    col = f"След {years} година" if years == 1 else f"След {years} години"
    pct_r2 = round(pct, 2)
    if factor >= 0:
        row_pct = f"{pct_r2:.2f}% по-висок"
        row_amt = f"+{fmt(monthly_delta)} повече на месец"
        row_year = f"Това прави +{fmt(yearly_delta)} на година"
    else:
        row_pct = f"{abs(pct_r2):.2f}% по-нисък"
        row_amt = f"-{fmt(abs(monthly_delta))} по-малко на месец"
        row_year = f"Това прави {fmt(yearly_delta)} на година"
    mapping = load_spending_ranges()
    delta_abs = abs(int(monthly_delta))
    _, delta_comparison = spending_range_insight(mapping, years, delta_abs)
    yearly_abs = abs(int(yearly_delta))
    _, yearly_delta_comparison = spending_range_insight(mapping, years, yearly_abs)
    return pd.DataFrame(
        {
            col: [
                row_will_be,
                row_pct,
                "",
                row_amt,
                delta_comparison,
                "",
                row_year,
                yearly_delta_comparison,
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
        f"Начален наем: {initial}",
        f"Сценарий: {scenario}",
        f"Ниво: {level}",
        f"Годишна промяна: {annual:.2%}",
        "Сложена промяна",
    ]
    summary = pd.DataFrame(rows, columns=["Обобщение"])
    st.dataframe(summary, hide_index=True, width="stretch")



def render_projection(projection_data: dict):
    st.success(f"💰 Месечният ви наем е: {fmt(projection_data['rent_value'])}")
    render_rent_projection_summary(projection_data)
    st.subheader("🏠 Наемът във времето")
    st.caption("👉 Как се променя наемът ви година след година")
    view_mode = st.radio(
        "Режим на проекцията",
        ["📋 Само таблица", "📊 Само графика"],
        horizontal=True,
        key="projection_view_mode",
        label_visibility="collapsed",
    )

    if view_mode == "📋 Само таблица":
        summary_df_display = projection_data["summary_df"].copy()
        summary_df_display["Месечен наем"] = summary_df_display[
            "Месечен наем"
        ].apply(fmt)
        summary_df_display["Годишен наем"] = summary_df_display[
            "Годишен наем"
        ].apply(fmt)
        st.dataframe(summary_df_display, width="stretch", hide_index=True)

        st.caption("Изберете година, за да видите как се променя наемът")
        rent_snap_pick = st.segmented_control(
            "Снимка на наема във времето",
            RENT_OVER_TIME_SNAPSHOT_LABELS,
            default=RENT_OVER_TIME_SNAPSHOT_LABELS[0],
            key="rent_over_time_snapshot_years",
            label_visibility="collapsed",
        )
        if rent_snap_pick:
            y_snap = parse_year_label(rent_snap_pick)
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

    summary_df = projection_data["summary_df"].copy()
    bar_labels = [
        "текуща година",
        "след 1 година",
        "след 2 години",
        "след 3 години",
        "след 5 години",
        "след 10 години",
        "след 15 години",
        "след 20 години",
        "след 30 години",
    ]
    summary_df["Етикет"] = bar_labels[: len(summary_df)]
    summary_df["Етикет"] = pd.Categorical(
        summary_df["Етикет"], categories=bar_labels, ordered=True
    )
    bar_df = summary_df.sort_values("Етикет").set_index("Етикет")[
        ["Месечен наем"]
    ]
    if view_mode == "📊 Само графика":
        st.bar_chart(bar_df)

    st.markdown("")

    st.subheader("💸 Общо платен наем")
    st.caption("👉 Колко плащате общо във времето")
    total_view_mode = st.radio(
        "Режим на общия разход",
        ["📋 Само таблица", "📊 Само графика"],
        horizontal=True,
        key="total_view_mode",
        label_visibility="collapsed",
    )
    if total_view_mode == "📋 Само таблица":
        total_spending_display = projection_data["total_spending_df"].copy()
        total_spending_display["Общо платено"] = total_spending_display[
            "Общо платено"
        ].apply(fmt)
        st.dataframe(total_spending_display, width="stretch", hide_index=True)

    total_labels = [
        "За 1 година",
        "За 2 години",
        "За 3 години",
        "За 5 години",
        "За 10 години",
        "За 15 години",
        "За 20 години",
        "За 30 години",
    ]
    total_df = projection_data["total_spending_df"].copy()
    total_df["Етикет"] = total_labels[: len(total_df)]
    total_df["Етикет"] = pd.Categorical(
        total_df["Етикет"], categories=total_labels, ordered=True
    )
    total_bar_df = (
        total_df.sort_values("Етикет")
        .set_index("Етикет")[["Общо платено"]]
    )
    if total_view_mode == "📊 Само графика":
        st.bar_chart(total_bar_df)

    mapping_spending = load_spending_ranges()
    st.caption("Изберете година, за да видите в какво се превръща наемът")
    horizon_pick = st.segmented_control(
        "Прозрение за разхода",
        TOTAL_RENT_INSIGHT_LABELS,
        default=TOTAL_RENT_INSIGHT_LABELS[0],
        key="total_rent_paid_insight_horizon",
        label_visibility="collapsed",
    )

    if horizon_pick:
        y = parse_year_label(horizon_pick)
        spent = total_spending_for_horizon_years(projection_data, y)
        after_line, comp_line = spending_range_insight(
            mapping_spending, y, abs(int(spent))
        )
        if after_line:
            st.write(after_line)
        if comp_line:
            st.write(comp_line)

    st.divider()

    st.subheader("📊 Тенденция на наема")
    st.caption("👉 Как расте наемът във времето, показан като крива")
    _d = chr(36)
    _legacy_projection_metrics = {
        f"Monthly Rent ({_d})": "Месечен наем",
        f"Annual Rent ({_d})": "Годишен наем",
        f"Total Spending ({_d})": "Общо платен наем",
        "Monthly Rent": "Месечен наем",
        "Annual Rent": "Годишен наем",
        "Total Rent Paid": "Общо платен наем",
    }
    _pcm = st.session_state.get("projection_chart_metric")
    if _pcm in _legacy_projection_metrics:
        st.session_state["projection_chart_metric"] = _legacy_projection_metrics[
            _pcm
        ]
    metric = st.radio(
        "Метрика за проекцията",
        ["Месечен наем", "Годишен наем", "Общо платен наем"],
        horizontal=True,
        key="projection_chart_metric",
        label_visibility="collapsed",
    )
    chart_col = "Общо платено" if metric == "Общо платен наем" else metric
    chart_df = projection_data["chart_df"].set_index("Година")
    st.line_chart(chart_df[[chart_col]])


st.caption("Въведете месечния си наем и натиснете ▶️ Старт")

rent_text = st.text_input(
    "💵 Месечен наем",
    value=st.session_state["rent"],
    placeholder="напр. 1200",
)
st.session_state["rent"] = rent_text

rent_value = None
error = None

if rent_text:
    try:
        clean = rent_text.replace(" ", "").replace(",", "")
        rent_value = int(clean)

        if rent_value < 0:
            error = "❗ Наемът трябва да е положителен"
        elif rent_value > MAX_RENT:
            error = (
                "❗ Наемът трябва да е под 1 000 000. "
                "Ако сте милионер, това приложение вероятно не е за вас 😄"
            )
    except ValueError:
        error = "❗ Моля, въведете валидно число"


scenario = st.radio(
    "Изберете сценарий",
    ["🟢 Оптимистичен", "🔵 Типичен", "🔴 Песимистичен", "⚫ Екстреми"],
    horizontal=True,
    key="adv_scenario",
)

if scenario == "🟢 Оптимистичен":
    level = st.radio("Изберете ниво на сценария", ["Много ниско", "Ниско"], horizontal=True, key="adv_level_opt")
elif scenario == "🔵 Типичен":
    level = st.radio(
        "Изберете ниво на сценария", ["Типично", "Средно"], horizontal=True, key="adv_level_typ"
    )
elif scenario == "🔴 Песимистичен":
    level = st.radio(
        "Изберете ниво на сценария", ["Високо", "Много високо"], horizontal=True, key="adv_level_pess"
    )
else:  # "⚫ Екстреми"
    level = st.radio(
        "Изберете ниво на сценария", ["Мин.", "Макс."], horizontal=True, key="adv_level_ext"
    )

stat_map = {
    "Много ниско": "p10",
    "Ниско": "p25",
    "Типично": "median",
    "Средно": "mean",
    "Високо": "p75",
    "Много високо": "p90",
    "Мин.": "min",
    "Макс.": "max",
}

preview_growth_rate = get_growth_rate_for_stat(stat_map[level])
st.caption(f"Годишна промяна: {preview_growth_rate:.2%}")

if st.button("▶️ Старт", type="primary", key="advanced_start"):
    if error:
        st.error(error)
    elif rent_value is None:
        st.error("❗ Моля, въведете наема си")
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
