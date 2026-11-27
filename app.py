from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure
import streamlit as st


st.set_page_config(
    page_title="DataLens | CSV Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #f5f7fb; }
    [data-testid="stHeader"] { background: rgba(245,247,251,.9); }
    [data-testid="stSidebar"] { background: #101828; }
    [data-testid="stSidebar"] * { color: #e7edf7; }
    [data-testid="stSidebar"] [data-baseweb="select"] * { color: #172033; }
    .hero {
        padding: 1.7rem 2rem; border-radius: 22px; color: white;
        background: linear-gradient(120deg, #172554 0%, #3730a3 52%, #0e7490 100%);
        margin: .2rem 0 1.5rem;
    }
    .hero h1 { font-family: 'Manrope', sans-serif; font-size: 2rem; margin: 0 0 .25rem; }
    .hero p { color: #dbeafe; margin: 0; font-size: 1rem; }
    [data-testid="stMetric"] {
        background: white; border: 1px solid #e8edf5; border-radius: 16px;
        padding: 1rem 1.2rem; box-shadow: 0 5px 18px rgba(27,39,68,.04);
    }
    div[data-testid="stTabs"] button { font-weight: 600; }
    .insight {
        background: white; border: 1px solid #e8edf5; border-left: 4px solid #6366f1;
        padding: .9rem 1rem; border-radius: 12px; margin: .45rem 0; color: #344054;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def read_csv_file(contents: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(contents), sep=None, engine="python")


def make_chart_layout(figure: Figure, title: str) -> Figure:
    figure.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
        template="plotly_white",
        margin={"l": 18, "r": 18, "t": 62, "b": 18},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "DM Sans, sans-serif", "color": "#344054"},
        legend_title_text="",
    )
    return figure


def get_column_groups(frame: pd.DataFrame) -> tuple[list[str], list[str]]:
    numeric = frame.select_dtypes(include="number").columns.tolist()
    categorical = [
        column
        for column in frame.columns
        if column not in numeric
        and (
            pd.api.types.is_object_dtype(frame[column])
            or isinstance(frame[column].dtype, pd.CategoricalDtype)
            or pd.api.types.is_bool_dtype(frame[column])
            or pd.api.types.is_string_dtype(frame[column])
        )
    ]
    return numeric, categorical


st.sidebar.markdown("## DataLens")
st.sidebar.caption("A clearer view of your CSV data")
uploaded_file = st.sidebar.file_uploader(
    "Upload a CSV file",
    type=["csv"],
    help="Your file is analyzed locally in this app session.",
)

sample_path = Path(__file__).with_name("synthetic_student_support.csv")
if uploaded_file is not None:
    source_name = uploaded_file.name
    try:
        original_data = read_csv_file(uploaded_file.getvalue())
    except (
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        ValueError,
    ) as error:
        st.error(f"Could not read **{source_name}** as a CSV: {error}")
        st.stop()
elif sample_path.is_file():
    source_name = sample_path.name
    try:
        original_data = read_csv_file(sample_path.read_bytes())
    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        ValueError,
    ) as error:
        st.error(f"Could not read the included demo CSV: {error}")
        st.stop()
else:
    st.markdown(
        """
        <div class="hero">
          <h1>Turn your CSV into a story.</h1>
          <p>Upload a dataset to explore its shape, quality, patterns, and relationships.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info("Upload a CSV file in the sidebar to get started.")
    st.stop()

if len(original_data.columns) == 0:
    st.error("This CSV has no columns. Check that the file includes a header row.")
    st.stop()
if original_data.empty:
    st.error("This CSV has column headers but no data rows.")
    st.stop()

numeric_columns, categorical_columns = get_column_groups(original_data)

st.sidebar.divider()
st.sidebar.markdown("### Explore a subset")
filtered_data = original_data.copy()

if categorical_columns:
    filter_column = st.sidebar.selectbox(
        "Category filter",
        ["No filter", *categorical_columns],
        help="Choose a category column, then select which values to include.",
    )
    if filter_column != "No filter":
        missing_label = "(Missing)"
        filter_values = original_data[filter_column].astype("string").fillna(missing_label)
        options = filter_values.unique().tolist()
        selected_values = st.sidebar.multiselect(
            "Values to include",
            options,
            default=options,
            key="category_filter_values",
        )
        if len(selected_values) != len(options):
            filtered_data = original_data.loc[filter_values.isin(selected_values)].copy()

if numeric_columns:
    range_column = st.sidebar.selectbox("Numeric range filter", ["No filter", *numeric_columns])
    if range_column != "No filter":
        values = original_data[range_column].dropna()
        if not values.empty:
            low, high = float(values.min()), float(values.max())
            if low < high:
                if pd.api.types.is_integer_dtype(original_data[range_column]):
                    selected_range = st.sidebar.slider(
                        f"{range_column} range",
                        min_value=int(low),
                        max_value=int(high),
                        value=(int(low), int(high)),
                    )
                else:
                    selected_range = st.sidebar.slider(
                        f"{range_column} range",
                        min_value=low,
                        max_value=high,
                        value=(low, high),
                    )
                filtered_data = filtered_data.loc[
                    filtered_data[range_column].between(*selected_range)
                    | filtered_data[range_column].isna()
                ].copy()

missing_cells = int(original_data.isna().sum().sum())
duplicate_rows = int(original_data.duplicated().sum())
missing_percent = missing_cells / original_data.size * 100 if original_data.size else 0

st.markdown(
    f"""
    <div class="hero">
      <h1>Your data, at a glance.</h1>
      <p>Exploring <strong>{source_name}</strong> · {len(original_data):,} rows ·
      {len(original_data.columns):,} columns</p>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_columns = st.columns(5)
metric_columns[0].metric("Rows in view", f"{len(filtered_data):,}")
metric_columns[1].metric("Columns", f"{len(original_data.columns):,}")
metric_columns[2].metric("Missing cells", f"{missing_cells:,}", f"{missing_percent:.1f}% of all cells")
metric_columns[3].metric("Duplicate rows", f"{duplicate_rows:,}")
metric_columns[4].metric("Numeric columns", f"{len(numeric_columns):,}")

overview_tab, explore_tab, quality_tab, data_tab = st.tabs(
    ["Overview", "Explore charts", "Data quality", "Data preview"]
)

with overview_tab:
    left, right = st.columns([1.55, 1])
    with left:
        if filtered_data.empty:
            st.info("No rows match the current filters. Adjust the sidebar filters to see the overview.")
        elif len(numeric_columns) >= 2:
            correlation = filtered_data[numeric_columns].corr(numeric_only=True)
            figure = px.imshow(
                correlation,
                text_auto=".2f",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                aspect="auto",
            )
            st.plotly_chart(
                make_chart_layout(figure, "Numeric correlation map"),
                use_container_width=True,
            )
        elif numeric_columns:
            figure = px.histogram(
                filtered_data,
                x=numeric_columns[0],
                nbins=25,
                marginal="box",
                color_discrete_sequence=["#6366f1"],
            )
            st.plotly_chart(
                make_chart_layout(figure, f"Distribution of {numeric_columns[0]}"),
                use_container_width=True,
            )
        else:
            st.info("No numeric columns were detected, so a correlation chart is not available.")

    with right:
        st.subheader("Quick read")
        insights = [
            f"The dataset contains **{len(original_data):,} rows** and **{len(original_data.columns):,} columns**."
        ]
        if missing_cells:
            most_missing = original_data.isna().sum().sort_values(ascending=False)
            column = str(most_missing.index[0])
            missing_count = int(most_missing.iloc[0])
            insights.append(
                f"**{column}** has the most missing values "
                f"({missing_count:,}, {missing_count / len(original_data) * 100:.1f}%)."
            )
        else:
            insights.append("There are **no missing cells** in this dataset.")
        if duplicate_rows:
            insights.append(f"Found **{duplicate_rows:,} duplicate rows**.")
        if len(numeric_columns) >= 2 and len(filtered_data) > 1:
            corr = filtered_data[numeric_columns].corr(numeric_only=True).abs()
            np.fill_diagonal(corr.values, np.nan)
            correlations = corr.stack()
            if not correlations.empty:
                pair = correlations.idxmax()
                strength = corr.loc[pair[0], pair[1]]
                insights.append(
                    f"Strongest numeric relationship: **{pair[0]}** and **{pair[1]}** "
                    f"(absolute correlation {strength:.2f}). Correlation does not imply causation."
                )
            else:
                insights.append("No numeric correlations could be calculated for the selected rows.")
        for insight in insights:
            st.markdown(f'<div class="insight">{insight}</div>', unsafe_allow_html=True)

    st.subheader("Column snapshot")
    snapshot = pd.DataFrame(
        {
            "Column": original_data.columns,
            "Type": [str(dtype) for dtype in original_data.dtypes],
            "Filled": [f"{original_data[column].notna().mean() * 100:.1f}%" for column in original_data],
            "Unique values": [int(original_data[column].nunique(dropna=True)) for column in original_data],
        }
    )
    st.dataframe(snapshot, use_container_width=True, hide_index=True)

with explore_tab:
    if filtered_data.empty:
        st.warning("No rows match the current filters. Adjust the sidebar filters to see charts.")
    else:
        chart_left, chart_right = st.columns(2)
        if numeric_columns:
            with chart_left:
                selected_numeric = st.selectbox("Numeric column", numeric_columns)
                distribution_type = st.radio(
                    "Distribution view",
                    ["Histogram", "Box plot"],
                    horizontal=True,
                )
                if distribution_type == "Histogram":
                    bins = st.slider("Histogram bins", 5, 60, 25)
                    figure = px.histogram(
                        filtered_data,
                        x=selected_numeric,
                        nbins=bins,
                        marginal="box",
                        color_discrete_sequence=["#6366f1"],
                    )
                else:
                    figure = px.box(
                        filtered_data,
                        y=selected_numeric,
                        points="outliers",
                        color_discrete_sequence=["#06b6d4"],
                    )
                st.plotly_chart(
                    make_chart_layout(figure, f"{distribution_type} · {selected_numeric}"),
                    use_container_width=True,
                )
        else:
            with chart_left:
                st.info("A distribution chart needs at least one numeric column.")

        if categorical_columns:
            with chart_right:
                selected_category = st.selectbox("Category column", categorical_columns)
                counts = (
                    filtered_data[selected_category]
                    .astype("string")
                    .fillna("(Missing)")
                    .value_counts()
                    .head(20)
                    .rename_axis(selected_category)
                    .reset_index(name="Count")
                )
                figure = px.bar(
                    counts.sort_values("Count"),
                    x="Count",
                    y=selected_category,
                    orientation="h",
                    color="Count",
                    color_continuous_scale="Viridis",
                )
                st.plotly_chart(
                    make_chart_layout(figure, f"Most common values · {selected_category}"),
                    use_container_width=True,
                )
        else:
            with chart_right:
                st.info("A category chart needs at least one non-numeric column.")

        if len(numeric_columns) >= 2:
            st.subheader("Explore relationships")
            relation_left, relation_right = st.columns(2)
            with relation_left:
                x_column = st.selectbox("X axis", numeric_columns, index=0)
            y_options = [column for column in numeric_columns if column != x_column]
            with relation_right:
                y_column = st.selectbox("Y axis", y_options)
            color_options = ["No color grouping", *categorical_columns]
            color_column = st.selectbox("Color by", color_options)
            figure = px.scatter(
                filtered_data,
                x=x_column,
                y=y_column,
                color=None if color_column == "No color grouping" else color_column,
                opacity=0.75,
                hover_data=filtered_data.columns[: min(6, len(filtered_data.columns))],
            )
            st.plotly_chart(
                make_chart_layout(figure, f"{x_column} vs {y_column}"),
                use_container_width=True,
            )
        elif numeric_columns and categorical_columns:
            st.subheader("Compare a measure by category")
            compare_left, compare_right = st.columns(2)
            with compare_left:
                measure = st.selectbox("Measure", numeric_columns, key="compare_measure")
            with compare_right:
                category = st.selectbox("Group", categorical_columns, key="compare_category")
            figure = px.box(
                filtered_data,
                x=category,
                y=measure,
                color=category,
                points="outliers",
            )
            st.plotly_chart(
                make_chart_layout(figure, f"{measure} by {category}"),
                use_container_width=True,
            )

with quality_tab:
    st.subheader("Completeness by column")
    quality = pd.DataFrame(
        {
            "Column": original_data.columns,
            "Data type": [str(dtype) for dtype in original_data.dtypes],
            "Non-null": [int(original_data[column].notna().sum()) for column in original_data],
            "Missing": [int(original_data[column].isna().sum()) for column in original_data],
            "Missing %": [
                original_data[column].isna().mean() * 100 if len(original_data) else 0
                for column in original_data
            ],
            "Unique": [int(original_data[column].nunique(dropna=True)) for column in original_data],
        }
    ).sort_values("Missing %", ascending=False)
    st.dataframe(
        quality,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Missing %": st.column_config.ProgressColumn(
                "Missing %",
                min_value=0,
                max_value=100,
                format="%.1f%%",
            )
        },
    )

    if numeric_columns:
        st.subheader("Potential outliers (IQR rule)")
        st.caption("Counts use the 1.5 × IQR rule. These are review candidates, not necessarily errors.")
        outlier_rows = []
        for column in numeric_columns:
            values = original_data[column].dropna()
            if values.empty:
                count = 0
            else:
                q1, q3 = values.quantile([0.25, 0.75])
                spread = q3 - q1
                count = int(((values < q1 - 1.5 * spread) | (values > q3 + 1.5 * spread)).sum())
            outlier_rows.append({"Column": column, "Potential outliers": count})
        st.dataframe(pd.DataFrame(outlier_rows), use_container_width=True, hide_index=True)

with data_tab:
    st.subheader("Filtered data")
    st.caption(f"Showing {len(filtered_data):,} of {len(original_data):,} rows.")
    st.dataframe(filtered_data.head(1000), use_container_width=True, hide_index=True)
    if len(filtered_data) > 1000:
        st.caption("The table is capped at 1,000 rows for readability. Download the full filtered data below.")

    download_left, download_right = st.columns(2)
    with download_left:
        st.download_button(
            "Download filtered data",
            data=filtered_data.to_csv(index=False).encode("utf-8"),
            file_name="datalens_filtered.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_right:
        st.download_button(
            "Download original data",
            data=original_data.to_csv(index=False).encode("utf-8"),
            file_name="datalens_original.csv",
            mime="text/csv",
            use_container_width=True,
        )
