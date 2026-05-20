import streamlit as st
import pandas as pd
import altair as alt

# ------------------------------------------------------------
# Page setting
# ------------------------------------------------------------
st.set_page_config(
    page_title="Food Shopping List Environmental Footprint Demo",
    layout="wide"
)

st.title("Food Shopping List Environmental Footprint Demo")

st.write(
    "Dropdown version: users select food items from the backend database, "
    "enter the amount, and calculate shopping-list-level environmental footprints."
)

# ------------------------------------------------------------
# 1. Load backend database
# ------------------------------------------------------------
impact_df = pd.read_csv("food_impact_factors.csv")

# 清理欄位名稱前後空白
impact_df.columns = impact_df.columns.str.strip()

# 檢查必要欄位
if "food_material" not in impact_df.columns:
    st.error("Error: food_impact_factors.csv must contain a column named 'food_material'.")
    st.stop()

# 如果沒有 display_name 欄位，就用 food_material 當顯示名稱
if "display_name" not in impact_df.columns:
    impact_df["display_name"] = impact_df["food_material"]

# 如果沒有 unit 欄位，就預設為 g
if "unit" not in impact_df.columns:
    impact_df["unit"] = "g"

# 建立下拉選單顯示名稱
# 例如：糙米 Husked rice (husked_rice)
impact_df["food_label"] = (
    impact_df["display_name"].astype(str)
    + "  ("
    + impact_df["food_material"].astype(str)
    + ")"
)

# ------------------------------------------------------------
# 2. Define EF 3.1 impact categories
# ------------------------------------------------------------
possible_impact_categories = [
    "climate_change",
    "acidification",
    "ecotoxicity_freshwater",
    "particulate_matter",
    "eutrophication_marine",
    "eutrophication_freshwater",
    "eutrophication_terrestrial",
    "human_toxicity_cancer",
    "human_toxicity_non_cancer",
    "ionising_radiation",
    "land_use",
    "ozone_depletion",
    "photochemical_ozone_formation",
    "resource_use_fossils",
    "resource_use_minerals_metals",
    "water_use"
]

# 只使用 CSV 裡真的存在的 impact categories
impact_categories = [
    category for category in possible_impact_categories
    if category in impact_df.columns
]

if len(impact_categories) == 0:
    st.error("Error: No EF impact category columns were found in food_impact_factors.csv.")
    st.stop()

# 把 impact 數值轉成數字，不能轉的就設成 0
for category in impact_categories:
    impact_df[category] = pd.to_numeric(impact_df[category], errors="coerce").fillna(0)

# 下拉選單選項
food_options = impact_df["food_label"].tolist()

# 建立對照表：前端顯示名稱 → 後台 food_material ID
label_to_material = dict(zip(impact_df["food_label"], impact_df["food_material"]))

# 建立對照表：後台 food_material ID → 前端顯示名稱
material_to_label = dict(zip(impact_df["food_material"], impact_df["food_label"]))


# ------------------------------------------------------------
# 3. Helper function
# ------------------------------------------------------------
def display_table_from_one(df):
    display_df = df.reset_index(drop=True).copy()
    display_df.index = display_df.index + 1
    st.dataframe(display_df, width="stretch")

def get_food_label(food_material_id):
    """
    Convert backend food_material ID to dropdown display label.
    If the ID does not exist in the database, use the first food option.
    """
    if food_material_id in material_to_label:
        return material_to_label[food_material_id]
    return food_options[0]


# ------------------------------------------------------------
# 4. Show backend database
# ------------------------------------------------------------
with st.expander("View Food Material Backend Database"):
    st.write(
        "This table is the backend food material environmental footprint database. "
        "The app reads this CSV file for calculation."
    )
    display_table_from_one(impact_df)


# ------------------------------------------------------------
# 5. Build preset shopping list scenarios
# ------------------------------------------------------------

# Scenario 1: Taiwanese pork rice basket
# 台式豬肉飯型：米飯 + 豬肉 + 蛋 + 蔬菜 + 大豆油
taiwanese_pork_rice_basket = pd.DataFrame({
    "Food item": [
        get_food_label("husked_rice"),
        get_food_label("pig_meat"),
        get_food_label("egg"),
        get_food_label("white_cabbage"),
        get_food_label("soybean_oil")
    ],
    "amount_g": [
        0.20,   # rice
        0.105,  # pork, about 3 servings of meat
        0.05,   # one egg
        0.12,   # vegetable
        0.01    # cooking oil
    ]
})

# Scenario 2: Western beef and dairy basket
# 西式牛肉乳品型：馬鈴薯 + 牛肉 + 牛奶 + 蔬菜 + 大豆油
western_beef_dairy_basket = pd.DataFrame({
    "Food item": [
        get_food_label("potato"),
        get_food_label("dairy_cow_meat"),
        get_food_label("cow_milk"),
        get_food_label("white_cabbage"),
        get_food_label("soybean_oil")
    ],
    "amount_g": [
        0.20,   # potato as staple food
        0.105,  # beef, about 3 servings of meat
        0.24,   # one cup of milk
        0.12,   # vegetable
        0.01    # cooking oil
    ]
})

# Scenario 3: Japanese fish rice basket
# 日式魚飯定食型：米飯 + 魚 + 蛋 + 蔬菜 + 少量油
japanese_fish_rice_basket = pd.DataFrame({
    "Food item": [
        get_food_label("husked_rice"),
        get_food_label("landed_fish"),
        get_food_label("egg"),
        get_food_label("white_cabbage"),
        get_food_label("soybean_oil")
    ],
    "amount_g": [
        0.20,   # rice
        0.105,  # fish, about 3 servings of protein
        0.05,   # one egg
        0.12,   # vegetable
        0.005   # lower cooking oil assumption
    ]
})

# Scenario 4: Plant-protein basket
# 植物蛋白型：米飯 + 大豆 + 蔬菜 + 大豆油
plant_protein_basket = pd.DataFrame({
    "Food item": [
        get_food_label("husked_rice"),
        get_food_label("soybean"),
        get_food_label("white_cabbage"),
        get_food_label("soybean_oil")
    ],
    "amount_g": [
        0.20,   # staple food
        0.105,  # soybean as plant protein
        0.15,   # higher vegetable amount
        0.01    # cooking oil
    ]
})

# Custom blank list
# 使用者可以自己從下拉選單選食材
custom_list = pd.DataFrame({
    "Food item": [
        food_options[0],
        food_options[0],
        food_options[0]
    ],
    "amount_g": [
        0.20,
        0.10,
        0.10
    ]
})

# Keep list_a and list_b aliases for old comparison code compatibility.
# 這兩行先保留，避免你前面已經寫好的 List A / List B comparison 區塊壞掉。
list_a = taiwanese_pork_rice_basket
list_b = western_beef_dairy_basket

# ------------------------------------------------------------
# Function: calculate results for a shopping list
# ------------------------------------------------------------
def calculate_list_results(input_list):
    """
    Calculate environmental footprint results for one shopping list.

    Input:
    - input_list: a dataframe with two columns:
      1. Food item
      2. amount_g

    Output:
    - merged_result: item-level calculation table
    - total_result: total footprint table across impact categories
    """

    temp_list = input_list.copy()

    # Remove empty rows
    temp_list = temp_list.dropna(subset=["Food item", "amount_g"])

    # Keep only rows with amount greater than 0
    temp_list = temp_list[temp_list["amount_g"] > 0]

    # Map dropdown food label to backend food_material ID
    temp_list["food_material"] = temp_list["Food item"].map(label_to_material)

    # Match with backend impact factor database
    merged_result = temp_list.merge(
        impact_df,
        on="food_material",
        how="left"
    )

    # Calculate impact for each impact category
    # Formula: amount_g × impact factor per g
    for category in impact_categories:
        merged_result[category + "_impact"] = (
            merged_result["amount_g"] * merged_result[category]
        )

    # Sum total impacts across all food items
    total_values = merged_result[
        [category + "_impact" for category in impact_categories]
    ].sum()

    total_values.index = impact_categories

    total_result = total_values.reset_index()
    total_result.columns = ["impact_category", "total_impact"]

    return merged_result, total_result

# ------------------------------------------------------------
# 6. Sidebar function selector
# ------------------------------------------------------------
st.sidebar.header("App Function")

app_mode = st.sidebar.radio(
    "Choose a function",
    [
        "Main function: Custom shopping list",
        "Auxiliary function: Preset scenarios"
    ]
)

if app_mode == "Main function: Custom shopping list":
    st.sidebar.info(
        "Main function: users create their own shopping list by selecting food items "
        "and entering the amount in g."
    )

    base_list = custom_list.copy()

else:
    st.sidebar.info(
        "Auxiliary function: preset scenarios are used to demonstrate cuisine-based "
        "shopping list comparison for the thesis demo."
    )

    preset_scenario = st.sidebar.selectbox(
        "Choose a preset scenario",
        [
            "Taiwanese pork rice basket",
            "Western beef and dairy basket",
            "Japanese fish rice basket",
            "Plant-protein basket"
        ]
    )

    if preset_scenario == "Taiwanese pork rice basket":
        base_list = taiwanese_pork_rice_basket.copy()
    elif preset_scenario == "Western beef and dairy basket":
        base_list = western_beef_dairy_basket.copy()
    elif preset_scenario == "Japanese fish rice basket":
        base_list = japanese_fish_rice_basket.copy()
    elif preset_scenario == "Plant-protein basket":
        base_list = plant_protein_basket.copy()


# ------------------------------------------------------------
# 7. Editable shopping list with dropdown
# ------------------------------------------------------------
st.subheader("1. Shopping List Input")

st.write(
    "Select food items from the dropdown menu and enter the amount in g. "
    "Using dropdown options prevents spelling errors and ensures every item exists in the backend database."
)

edited_list = st.data_editor(
    base_list,
    num_rows="dynamic",
    hide_index=True,
    width="stretch",
    column_config={
        "Food item": st.column_config.SelectboxColumn(
            "Food item",
            help="Select a food item from the backend database.",
            options=food_options,
            required=True,
            width="large"
        ),
        "amount_g": st.column_config.NumberColumn(
            "Amount (g)",
            help="Enter the amount of the selected food item in g.",
            min_value=0.0,
            step=0.1,
            format="%.3f",
            required=True,
            width="medium"
        )
    }
)

shopping_list = edited_list.copy()

# 移除空白列
shopping_list = shopping_list.dropna(subset=["Food item", "amount_g"])

# 只保留重量大於 0 的列
shopping_list = shopping_list[shopping_list["amount_g"] > 0]

if len(shopping_list) == 0:
    st.warning("Please select at least one food item and enter an amount greater than 0.")
    st.stop()

# 將前端顯示名稱轉成後台 food_material ID
shopping_list["food_material"] = shopping_list["Food item"].map(label_to_material)


# ------------------------------------------------------------
# 8. Show mapping result
# ------------------------------------------------------------
st.subheader("2. Food Item Mapping Result")

st.write(
    "This table shows how selected food items are mapped to backend food_material IDs."
)

display_table_from_one(
    shopping_list[["Food item", "food_material", "amount_g"]]
)


# ------------------------------------------------------------
# 9. Match shopping list with backend database
# ------------------------------------------------------------
merged = shopping_list.merge(
    impact_df,
    on="food_material",
    how="left"
)

missing_rows = merged[merged["unit"].isna()]

if len(missing_rows) > 0:
    st.error(
        "Some selected food items were not found in the backend database. "
        "Please check food_impact_factors.csv."
    )
    display_table_from_one(missing_rows)
    st.stop()


# ------------------------------------------------------------
# 10. Calculate impacts
# Formula: amount_g × impact factor per g
# ------------------------------------------------------------
for category in impact_categories:
    merged[category + "_impact"] = merged["amount_g"] * merged[category]

impact_cols = [category + "_impact" for category in impact_categories]

total_impacts = merged[impact_cols].sum()
total_impacts.index = impact_categories

total_table = total_impacts.reset_index()
total_table.columns = ["impact_category", "total_impact"]


# ------------------------------------------------------------
# 11. Total environmental footprint
# ------------------------------------------------------------
st.subheader("3. Shopping List Environmental Footprint")

st.write(
    "The table below shows the total environmental footprint of the selected shopping list "
    "across available EF 3.1 impact categories."
)

display_table_from_one(total_table)

st.write("Normalized profile chart for visualization:")

max_total = total_table["total_impact"].max()

if max_total > 0:
    total_table["normalized_value"] = total_table["total_impact"] / max_total * 100
else:
    total_table["normalized_value"] = 0

st.bar_chart(
    total_table.set_index("impact_category")["normalized_value"]
)

st.caption(
    "The EF impact categories have different units and scales. "
    "Original values are kept in the table. "
    "The chart uses normalized values for easier visualization."
)


# ------------------------------------------------------------
# 12. Item contribution and hotspot analysis
# ------------------------------------------------------------
st.subheader("4. Item Contribution and Hotspot Analysis")

selected_category = st.selectbox(
    "Select one impact category for item contribution analysis",
    impact_categories,
    index=0
)

selected_col = selected_category + "_impact"

contribution = merged[
    ["Food item", "food_material", "amount_g", selected_col]
].copy()

contribution = contribution.sort_values(selected_col, ascending=False)

total_selected_impact = contribution[selected_col].sum()

if total_selected_impact > 0:
    contribution["contribution_percent"] = (
        contribution[selected_col] / total_selected_impact * 100
    )
else:
    contribution["contribution_percent"] = 0

st.write(f"Item contribution for: **{selected_category}**")

display_table_from_one(contribution)

st.bar_chart(
    contribution.set_index("Food item")["contribution_percent"]
)

hotspot_item = contribution.iloc[0]["Food item"]
hotspot_percent = contribution.iloc[0]["contribution_percent"]

st.success(
    f"Hotspot result: **{hotspot_item}** is the largest contributor to "
    f"**{selected_category}**, accounting for approximately "
    f"**{hotspot_percent:.1f}%** of this shopping list impact."
)


# ------------------------------------------------------------
# 13. Cross-category hotspot summary
# ------------------------------------------------------------
st.subheader("5. Cross-Category Hotspot Summary")

hotspot_rows = []

for category in impact_categories:
    col = category + "_impact"

    temp = merged[
        ["Food item", "food_material", col]
    ].copy()

    temp = temp.sort_values(col, ascending=False)

    top_food = temp.iloc[0]["Food item"]
    top_value = temp.iloc[0][col]
    total_value = temp[col].sum()

    if total_value > 0:
        top_percent = top_value / total_value * 100
    else:
        top_percent = 0

    hotspot_rows.append({
        "impact_category": category,
        "hotspot_food": top_food,
        "contribution_percent": round(top_percent, 1)
    })

hotspot_df = pd.DataFrame(hotspot_rows)

st.write(
    "This table shows which food item contributes the most in each impact category."
)

display_table_from_one(hotspot_df)


# ------------------------------------------------------------
# 14. Four preset scenario comparison table
# ------------------------------------------------------------
if app_mode == "Auxiliary function: Preset scenarios":

    st.subheader("6. Four Preset Scenario Comparison")
    st.write(
        "This table compares the environmental footprints of four simplified cuisine-based "
        "shopping list scenarios. Each row represents one EF impact category. "
        "The comparison should be interpreted within the same impact category because different "
        "impact categories have different units."
    )

    # Define four preset scenarios
    preset_scenarios = {
        "Taiwanese pork rice basket": taiwanese_pork_rice_basket,
        "Western beef and dairy basket": western_beef_dairy_basket,
        "Japanese fish rice basket": japanese_fish_rice_basket,
        "Plant-protein basket": plant_protein_basket
    }

    # Calculate total impacts for each scenario
    scenario_total_tables = []

    for scenario_name, scenario_list in preset_scenarios.items():
        merged_scenario, total_scenario = calculate_list_results(scenario_list)

        total_scenario = total_scenario.rename(
            columns={"total_impact": scenario_name}
        )

        scenario_total_tables.append(total_scenario)

    # Merge all scenario results into one comparison table
    four_scenario_comparison = scenario_total_tables[0]

    for table in scenario_total_tables[1:]:
        four_scenario_comparison = four_scenario_comparison.merge(
            table,
            on="impact_category",
            how="inner"
        )

    scenario_names = list(preset_scenarios.keys())

    # Identify lowest and highest scenario for each impact category
    four_scenario_comparison["Lowest impact scenario"] = (
        four_scenario_comparison[scenario_names].idxmin(axis=1)
    )

    four_scenario_comparison["Highest impact scenario"] = (
        four_scenario_comparison[scenario_names].idxmax(axis=1)
    )

    # Round numeric values for display
    four_scenario_display = four_scenario_comparison.copy()

    for scenario_name in scenario_names:
        four_scenario_display[scenario_name] = four_scenario_display[scenario_name].round(6)

    st.write("### 6.1 Four-scenario footprint comparison table")

    display_table_from_one(four_scenario_display)

    st.caption(
        "Lowest and highest scenarios are identified within each impact category. "
        "This avoids comparing raw values across different EF categories, since each category has a different unit."
    )

    # ------------------------------------------------------------
    # 14-1. Four-scenario comparison chart by selected category
    # ------------------------------------------------------------
    st.write("### 6.2 Scenario Comparison by Selected Impact Category")

    st.write(
        "Select one impact category to compare the four preset scenarios. "
        "This chart compares scenarios within the same impact category, so the values are easier to interpret."
    )

    selected_scenario_category = st.selectbox(
        "Select one impact category",
        impact_categories,
        index=0,
        key="four_scenario_selected_category"
    )

    selected_row = four_scenario_comparison[
        four_scenario_comparison["impact_category"] == selected_scenario_category
    ].iloc[0]

    scenario_chart_df = pd.DataFrame({
        "Scenario": scenario_names,
        "Impact value": [selected_row[scenario_name] for scenario_name in scenario_names]
    })

    scenario_chart_df = scenario_chart_df.sort_values("Impact value", ascending=False)

    st.write(f"Comparison for: **{selected_scenario_category}**")

    display_table_from_one(scenario_chart_df)

    st.bar_chart(
        scenario_chart_df.set_index("Scenario")["Impact value"]
    )

    highest_scenario = scenario_chart_df.iloc[0]["Scenario"]
    highest_value = scenario_chart_df.iloc[0]["Impact value"]

    lowest_scenario = scenario_chart_df.iloc[-1]["Scenario"]
    lowest_value = scenario_chart_df.iloc[-1]["Impact value"]

    st.success(
        f"For **{selected_scenario_category}**, the highest-impact scenario is "
        f"**{highest_scenario}**, while the lowest-impact scenario is **{lowest_scenario}**."
    )

    st.caption(
        "This chart only compares scenarios within one selected impact category. "
        "It should not be used to compare values across different impact categories, because EF categories have different units."
    )

    # ------------------------------------------------------------
    # 14-2. Hotspot summary by scenario
    # ------------------------------------------------------------
    st.write("### 6.3 Hotspot Summary by Scenario")

    st.write(
        "This table identifies the main contributing food item within each preset scenario "
        "for the selected impact category."
    )

    hotspot_summary_rows = []

    for scenario_name, scenario_list in preset_scenarios.items():
        merged_scenario, total_scenario = calculate_list_results(scenario_list)

        selected_col = selected_scenario_category + "_impact"

        item_hotspot_table = merged_scenario[
            ["Food item", "food_material", "amount_g", selected_col]
        ].copy()

        item_hotspot_table = item_hotspot_table.sort_values(
            selected_col,
            ascending=False
        )

        scenario_total_impact = item_hotspot_table[selected_col].sum()

        if scenario_total_impact > 0:
            hotspot_contribution_percent = (
                item_hotspot_table.iloc[0][selected_col] / scenario_total_impact * 100
            )
        else:
            hotspot_contribution_percent = 0

        hotspot_summary_rows.append({
            "scenario": scenario_name,
            "impact_category": selected_scenario_category,
            "hotspot_food": item_hotspot_table.iloc[0]["Food item"],
            "backend_food_material": item_hotspot_table.iloc[0]["food_material"],
            "amount_g": round(item_hotspot_table.iloc[0]["amount_g"], 3),
            "contribution_percent": round(hotspot_contribution_percent, 1)
        })

    hotspot_summary_df = pd.DataFrame(hotspot_summary_rows)

    display_table_from_one(
        hotspot_summary_df
    )

    st.caption(
        "The hotspot food is the item with the largest contribution within each scenario "
        "for the selected impact category."
    )


if app_mode == "Auxiliary function: Preset scenarios":
    st.subheader("7. AI-Assisted Explanation Prototype")
else:
    st.subheader("6. AI-Assisted Explanation Prototype")

def get_hotspot_for(category_name):
    row = hotspot_df[hotspot_df["impact_category"] == category_name]
    if len(row) > 0:
        return row.iloc[0]["hotspot_food"]
    return "N/A"

climate_hotspot = get_hotspot_for("climate_change")
water_hotspot = get_hotspot_for("water_use")
land_hotspot = get_hotspot_for("land_use")

explanation = f"""
In this shopping list, **{climate_hotspot}** is the main contributor to climate change impact.
For water use, the main hotspot is **{water_hotspot}**.
For land use, the main hotspot is **{land_hotspot}**.

This result shows that the major environmental hotspot may change across different impact categories.
Therefore, a single carbon indicator may not fully represent the environmental profile of food consumption.

This prototype demonstrates how a shopping list can be connected with a food material impact factor database
to provide approximate environmental footprint reporting and consumer-facing feedback.
"""

st.info(explanation)

st.caption(
    "This is a first MVP prototype. The explanation is currently rule-based. "
    "In the next version, this module can be connected to an LLM agent."
)

#calculate the kalories for a given recipe of food material amounts, and then give suggestions on how to adjust the recipe to meet a target kalorie level.

