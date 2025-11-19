import streamlit as st
import json
import os
import pandas as pd
import random

# TODO delete old recipe when adjusting
# TODO add delete button
# TODO generate desktop icon
# TODO add rectangle around filter and sorting
# TODO create git repo
# TODO add image instead of text fields
# TODO automatic push when saving new recipe

# --- Load recipes ---
def load_recipes():
    recipes = []
    for file in os.listdir(RECIPE_DIR):
        if file.endswith(".json"):
            with open(os.path.join(RECIPE_DIR, file), "r") as f:
                try:
                    recipes.append(json.load(f))
                except json.JSONDecodeError:
                    st.warning(f"Could not read {file}")
    return recipes

def classify_duration(minutes: int) -> str:
    if minutes < 15:
        return "Short"
    elif 15 <= minutes <= 30:
        return "Medium"
    else:
        return "Long"

# -----------------------------------------------

ALLOWED_CATEGORIES = ["Vegetarian", "Vegan", "Fish", "Meat"]
ALLOWED_DURATIONS = ["Short", "Medium", "Long"]

# -----------------------------------------------

RECIPE_DIR = "recipes"
os.makedirs(RECIPE_DIR, exist_ok=True)
st.set_page_config(page_title="My Cookbook", layout="wide", initial_sidebar_state="expanded")

recipes = load_recipes()
recipe_names = [r["name"] for r in recipes]

recipe_df = pd.DataFrame([{
    "Name": r["name"],
    "Category": r.get("category", "").capitalize() if r.get("category") else "Other",
    "Instructions": r.get("instructions", ""),
    "Ingredients": r.get("ingredients", ""),
    "Duration": classify_duration(r.get("duration", -1))
} for r in recipes])

# --- Sidebar: search + filter ---
st.sidebar.title("🥘 My Cookbook Sidebar")
search_query = st.sidebar.text_input("🔍 Search recipes")

# Multi-select for categories
selected_cats = st.sidebar.multiselect("Filter by Category", options=ALLOWED_CATEGORIES, default=ALLOWED_CATEGORIES)

# Multi-select for durations
selected_durations = st.sidebar.multiselect("Filter by Duration", options=ALLOWED_DURATIONS, default=ALLOWED_DURATIONS)

# --- Sidebar: sort recipes ---
sort_field = st.sidebar.selectbox("Sorted by", options=["Name", "Category", "Duration"], index=0)

# Apply filters
# filtered_df = recipe_df[
#     recipe_df["Category"].isin(selected_cats) &
#     recipe_df["Duration"].isin(selected_durations)
# ]

if recipe_df.empty:
    st.sidebar.info("No recipes found.")
    filtered_df = pd.DataFrame(columns=["Name", "Category", "Duration"])
else:
    filtered_df = recipe_df[
        recipe_df["Category"].isin(selected_cats) &
        recipe_df["Duration"].isin(selected_durations)
    ]

if search_query:
    q = search_query.strip().lower()  # lowercase for case-insensitive search

    def row_matches(row):
        # Check Name, Category, Duration as strings
        for col in ["Name", "Category", "Duration"]:
            if q in str(row.get(col, "")).lower():
                return True
        # Check ingredients list
        if any(q in str(ing).lower() for ing in row.get("Ingredients", [])):
            return True
        # Check instructions list
        if any(q in str(step).lower() for step in row.get("Instructions", [])):
            return True
        return False

    mask = filtered_df.apply(row_matches, axis=1)
    filtered_df = filtered_df[mask]

# --- Apply sorting ---
if sort_field == "Duration":
    # Map classified duration to numeric order for correct ascending sort
    duration_order = {"Short": 0, "Medium": 1, "Long": 2}
    filtered_df["Duration_order"] = filtered_df["Duration"].map(duration_order)
    filtered_df = filtered_df.sort_values(by="Duration_order", ascending=True).drop(columns=["Duration_order"])
else:
    filtered_df = filtered_df.sort_values(by=sort_field, ascending=True)


# --- Set a random recipe as initial page if none selected ---
if "selected_recipe" not in st.session_state and not st.session_state.get("show_add_recipe", False):
    if len(filtered_df) > 0:
        st.session_state.selected_recipe = random.choice(filtered_df["Name"].tolist())
        st.session_state.just_random = True  # mark that this is a random recipe
    else:
        st.session_state.selected_recipe = None

# --- Sidebar: buttons in the same row ---
col1, col2 = st.sidebar.columns([1, 1])  # Two equal columns

with col1:
    if st.button("🎲 Random Recipe", width="stretch"):
        if len(filtered_df) > 0:
            random_recipe = random.choice(filtered_df["Name"].tolist())
            st.session_state.selected_recipe = random_recipe
            st.session_state.show_add_recipe = False
            st.session_state.random_message = f"🎉 Your random recipe for today: **{random_recipe}**"
        else:
            st.sidebar.warning("No recipes found for this filter.")

with col2:
    if st.button("➕ New Recipe", width="stretch"):
        st.session_state.show_add_recipe = True
        st.session_state.selected_recipe = None

# --- Sidebar: clickable recipe list ---
st.sidebar.subheader("Recipes")
max_name_len = max((len(name) for name in filtered_df["Name"]), default=0)

for idx, row in filtered_df.iterrows():
    col1, col2, col3 = st.sidebar.columns([2, 1, 1])  # Name column wider
    padded_name = row["Name"].ljust(max_name_len)
    with col1:
        if st.button(padded_name, key=row["Name"], width="stretch"):
            st.session_state.selected_recipe = row["Name"]
            st.session_state.show_add_recipe = False
    with col2:
        st.markdown(
            f"""
            <div style='text-align:center; color:gray;
                        line-height:2.5em;'>  <!-- Adjust 2.5em for height -->
                {row['Category']}
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
            <div style='text-align:center; color:gray;
                        line-height:2.5em;'>
                {row.get('Duration', '')}
            </div>
            """,
            unsafe_allow_html=True
        )

# # --- Main page ---
# if st.session_state.get("show_add_recipe", False):
#     # Show Add Recipe form
#     st.title("➕ Add a new recipe")
#     name = st.text_input("Recipe name", key="new_name")
#     category = st.selectbox("Category", [""] + ALLOWED_CATEGORIES, key="new_category")
#     duration = st.number_input("Duration (min)", min_value=1, max_value=500, value=20, step=1, key="new_duration")
#     ingredients = st.text_area("Ingredients (one per line)", key="new_ingredients").splitlines()
#     instructions = st.text_area("Instructions (one per line)", key="new_instructions").splitlines()
#
#     if st.button("Save recipe"):
#         if not name:
#             st.error("Recipe name required.")
#         elif category == "":
#             st.error("Category required.")
#         else:
#             # Save the recipe
#             recipe_data = {
#                 "name": name,
#                 "category": category,
#                 "duration": duration,
#                 "ingredients": ingredients,
#                 "instructions": instructions
#             }
#             file_path = os.path.join(RECIPE_DIR, f"{name.lower().replace(' ', '_')}.json")
#             with open(file_path, "w") as f:
#                 json.dump(recipe_data, f, indent=4)
#             st.success(f"Saved {name}!")
#
#             # --- Update session state to show the new recipe ---
#             st.session_state.selected_recipe = name
#             st.session_state.show_add_recipe = False
#
#             # --- Rerun the app to clear inputs and show the new recipe page ---
#             st.rerun()
#
# elif st.session_state.get("selected_recipe", None):
#     recipe_name = st.session_state.selected_recipe
#     recipe = next(r for r in recipes if r["name"] == recipe_name)
#
#     # Display a success message above the header if this was randomly selected
#     if st.session_state.get("just_random", False):
#         st.success(f"🎉 Your random recipe for today: **{recipe_name}**")
#         st.session_state["just_random"] = False  # only show once
#
#     st.title(recipe["name"])
#
#     category = recipe.get("category", "N/A")
#     duration = recipe.get("duration", "N/A")
#     st.markdown(
#         f"<div style='font-size:16px; color:gray;'>{category} | {duration} min</div>",
#         unsafe_allow_html=True
#     )
#
#     st.subheader("Ingredients")
#     st.markdown("\n".join(f"- {i}" for i in recipe.get("ingredients", [])))
#     st.subheader("Instructions")
#     for step in recipe.get("instructions", []):
#         st.write(f"✅ {step}")

# --- Main page: Add / View / Edit recipe ---

# --- Add new recipe ---
if st.session_state.get("show_add_recipe", False):
    st.title("➕ Add a new recipe")

    name = st.text_input("Recipe name", key="new_name")
    category = st.selectbox("Category", [""] + ALLOWED_CATEGORIES, key="new_category")
    duration = st.number_input("Duration (min)", min_value=1, max_value=500, value=20, step=1, key="new_duration")
    ingredients = st.text_area("Ingredients (one per line)", key="new_ingredients").splitlines()
    instructions = st.text_area("Instructions (one per line)", key="new_instructions").splitlines()

    if st.button("Save recipe"):
        if not name:
            st.error("Recipe name required.")
        elif category == "":
            st.error("Category required.")
        else:
            # Save new recipe
            recipe_data = {
                "name": name,
                "category": category,
                "duration": duration,
                "ingredients": ingredients,
                "instructions": instructions
            }
            file_path = os.path.join(RECIPE_DIR, f"{name.lower().replace(' ', '_')}.json")
            with open(file_path, "w") as f:
                json.dump(recipe_data, f, indent=4)

            st.success(f"Saved {name}!")

            # Update session state
            st.session_state.selected_recipe = name
            st.session_state.show_add_recipe = False

            # Rerun to refresh
            st.rerun()


# --- View / Edit existing recipe ---
elif st.session_state.get("selected_recipe", None):
    recipe_name = st.session_state.selected_recipe
    recipe = next(r for r in recipes if r["name"] == recipe_name)

    # Display random recipe message if applicable
    if st.session_state.get("just_random", False):
        st.success(f"🎉 Your random recipe for today: **{recipe_name}**")
        st.session_state["just_random"] = False

    st.title(recipe["name"])

    category = recipe.get("category", "N/A")
    duration = recipe.get("duration", "N/A")
    st.markdown(f"<div style='font-size:16px; color:gray;'>{category.capitalize()} | {duration} min</div>", unsafe_allow_html=True)

    # --- Checkbox to toggle edit mode ---
    st.checkbox("✏️ Edit Mode", key="show_edit_recipe")

    if st.session_state.show_edit_recipe:
        st.subheader("Edit Recipe")

        # Editable recipe name
        name = st.text_input("Recipe name", value=recipe["name"], key="edit_name")

        cat_value = recipe.get("category", "").capitalize()
        if cat_value in ALLOWED_CATEGORIES:
            cat_index = ALLOWED_CATEGORIES.index(cat_value) + 1
        else:
            cat_index = 0  # fallback to first option

        # Other editable fields
        category = st.selectbox(
            "Category",
            [""] + ALLOWED_CATEGORIES,
            index=cat_index,
            key="edit_category"
        )
        duration = st.number_input(
            "Duration (min)",
            min_value=1,
            max_value=500,
            value=recipe.get("duration", 20),
            step=1,
            key="edit_duration"
        )
        ingredients = st.text_area(
            "Ingredients (one per line)",
            value="\n".join(recipe.get("ingredients", [])),
            key="edit_ingredients"
        ).splitlines()
        instructions = st.text_area(
            "Instructions (one per line)",
            value="\n".join(recipe.get("instructions", [])),
            key="edit_instructions"
        ).splitlines()

        if st.button("Save changes"):
            # Validate inputs
            if not name.strip():
                st.error("Recipe name required.")
            elif category == "":
                st.error("Category required.")
            else:
                # Paths for old and new files
                old_file_path = os.path.join(RECIPE_DIR, f"{recipe_name.lower().replace(' ', '_')}.json")
                new_file_path = os.path.join(RECIPE_DIR, f"{name.lower().replace(' ', '_')}.json")

                # Updated recipe data
                updated_recipe = {
                    "name": name,
                    "category": category,
                    "duration": duration,
                    "ingredients": ingredients,
                    "instructions": instructions
                }

                # Save new file
                with open(new_file_path, "w") as f:
                    json.dump(updated_recipe, f, indent=4)

                # Delete old file if name changed
                if old_file_path != new_file_path and os.path.exists(old_file_path):
                    os.remove(old_file_path)

                st.success(f"Updated recipe: {name}")
                st.session_state.selected_recipe = name

                # --- Reset edit mode safely ---
                if "show_edit_recipe" in st.session_state:
                    del st.session_state["show_edit_recipe"]

                # Reload recipes
                recipes = load_recipes()
                st.rerun()

    else:
        # Display recipe normally
        st.subheader("Ingredients")
        st.markdown("\n".join(f"- {i}" for i in recipe.get("ingredients", [])))
        st.subheader("Instructions")
        for step in recipe.get("instructions", []):
            st.write(f"✅ {step}")


#### Example recipe
# {
#     "name": "Asian Food",
#     "category": "vegetarian",
#     "ingredients": [
#         "Milch"
#     ],
#     "description": "Eat fast.",
#     "instructions": [
#         "buy ingredients",
#         "cook",
#         "eat"
#     ],
#     "duration": 15
# }