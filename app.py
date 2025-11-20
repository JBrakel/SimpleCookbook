import streamlit as st
import json
import os
import pandas as pd
import random

import base64
import requests

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

def delete_recipe(file_name: str):
    file_path = os.path.join(RECIPE_DIR, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def classify_duration(minutes: int) -> str:
    if minutes < 15:
        return "Short"
    elif 15 <= minutes <= 30:
        return "Medium"
    else:
        return "Long"

def upload_to_github(file_path, content_string):
    """
    Uploads or updates a file in the GitHub repo using the GitHub API.
    """

    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    branch = st.secrets.get("GITHUB_BRANCH", "main")

    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"

    # Check if file already exists (for update)
    get_response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )

    if get_response.status_code == 200:
        sha = get_response.json()["sha"]
    else:
        sha = None

    # Prepare payload for GitHub API
    payload = {
        "message": f"Update {file_path}",
        "content": base64.b64encode(content_string.encode()).decode(),
        "branch": branch
    }

    if sha:
        payload["sha"] = sha

    # Upload
    put_response = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )

    if put_response.status_code not in (200, 201):
        st.error(f"❌ Error uploading to GitHub: {put_response.text}")
    else:
        st.success(f"📤 Synced {file_path} to GitHub")

def delete_from_github(file_path):
    """
    Deletes a file from the GitHub repo using the GitHub API.
    """
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    branch = st.secrets.get("GITHUB_BRANCH", "main")

    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"

    # Get SHA of the file (required for deletion)
    get_response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )

    if get_response.status_code != 200:
        st.warning(f"File {file_path} not found on GitHub.")
        return

    sha = get_response.json()["sha"]

    payload = {
        "message": f"Delete {file_path}",
        "sha": sha,
        "branch": branch
    }

    delete_response = requests.delete(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )

    if delete_response.status_code not in (200, 201):
        st.error(f"❌ Error deleting from GitHub: {delete_response.text}")
    else:
        st.success(f"🗑️ Deleted {file_path} from GitHub")

# -----------------------------------------------

ALLOWED_CATEGORIES = ["Vegetarian", "Vegan", "Fish", "Meat"]
ALLOWED_DURATIONS = ["Short", "Medium", "Long"]

# -----------------------------------------------

RECIPE_DIR = "recipes"
os.makedirs(RECIPE_DIR, exist_ok=True)
st.set_page_config(page_title="Simple Cookbook", layout="wide", initial_sidebar_state="expanded")

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
st.sidebar.title("🥘Simple Cookbook Sidebar")
search_query = st.sidebar.text_input("🔍 Search recipes")

# Multi-select for categories
selected_cats = st.sidebar.multiselect("Filter by Category", options=ALLOWED_CATEGORIES, default=ALLOWED_CATEGORIES)

# Multi-select for durations
selected_durations = st.sidebar.multiselect("Filter by Duration", options=ALLOWED_DURATIONS, default=ALLOWED_DURATIONS)

# --- Sidebar: sort recipes ---
# sort_field = st.sidebar.selectbox("Sorted by", options=["Name", "Category", "Duration"], index=0)

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

# --- Top-right buttons (Random Recipe + New Recipe) ---

# CSS to place the top bar
st.markdown("""
    <style>
        .top-right-buttons {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            padding: 10px 5px;
        }
    </style>
""", unsafe_allow_html=True)

top_bar = st.container()
with top_bar:
    st.markdown('<div class="top-right-buttons">', unsafe_allow_html=True)

    cols_top = st.columns([7, 1, 1])

    with cols_top[1]:
        if st.button("➕ New", key="top_new", width="stretch"):
            st.session_state.show_add_recipe = True
            st.session_state.selected_recipe = None

    with cols_top[2]:
        if st.button("🎲 Random", key="top_random", width="stretch"):
            if len(filtered_df) > 0:
                random_recipe = random.choice(filtered_df["Name"].tolist())
                st.session_state.selected_recipe = random_recipe
                st.session_state.show_add_recipe = False
                st.session_state.random_message = f"🎉 Your random recipe for today: **{random_recipe}**"
            else:
                st.warning("No recipes found for this filter.")

    st.markdown('</div>', unsafe_allow_html=True)


# # --- Apply sorting ---
# if sort_field == "Duration":
#     # Map classified duration to numeric order for correct ascending sort
#     duration_order = {"Short": 0, "Medium": 1, "Long": 2}
#     filtered_df["Duration_order"] = filtered_df["Duration"].map(duration_order)
#     filtered_df = filtered_df.sort_values(by="Duration_order", ascending=True).drop(columns=["Duration_order"])
# else:
#     filtered_df = filtered_df.sort_values(by=sort_field, ascending=True)

# --- Always sort by Name → Category → Duration ---
duration_order = {"Short": 0, "Medium": 1, "Long": 2}
filtered_df["Duration_order"] = filtered_df["Duration"].map(duration_order)

filtered_df = filtered_df.sort_values(
    by=["Name", "Category", "Duration_order"],
    ascending=[True, True, True]
).drop(columns=["Duration_order"])


# --- Set a random recipe as initial page if none selected ---
if "selected_recipe" not in st.session_state and not st.session_state.get("show_add_recipe", False):
    if len(filtered_df) > 0:
        st.session_state.selected_recipe = random.choice(filtered_df["Name"].tolist())
        st.session_state.just_random = True  # mark that this is a random recipe
    else:
        st.session_state.selected_recipe = None

# # --- Sidebar: buttons in the same row ---
# col1, col2 = st.sidebar.columns([1, 1])  # Two equal columns
#
# with col1:
#     if st.button("🎲 Random Recipe", width="stretch"):
#         if len(filtered_df) > 0:
#             random_recipe = random.choice(filtered_df["Name"].tolist())
#             st.session_state.selected_recipe = random_recipe
#             st.session_state.show_add_recipe = False
#             st.session_state.random_message = f"🎉 Your random recipe for today: **{random_recipe}**"
#         else:
#             st.sidebar.warning("No recipes found for this filter.")
#
# with col2:
#     if st.button("➕ New Recipe", width="stretch"):
#         st.session_state.show_add_recipe = True
#         st.session_state.selected_recipe = None

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

# --- Main page: Add / View / Edit recipe ---
# --- Add new recipe ---
if st.session_state.get("show_add_recipe", False):
    st.title("➕ Add a new recipe")

    name = st.text_input("Recipe name", key="new_name")
    category = st.selectbox("Category", [""] + ALLOWED_CATEGORIES, key="new_category")
    duration = st.number_input("Duration (min)", min_value=1, max_value=500, value=20, step=1, key="new_duration")
    ingredients = st.text_area("Ingredients (one per line)", key="new_ingredients").splitlines()
    instructions = st.text_area("Instructions (one per line)", key="new_instructions").splitlines()

    cols = st.columns([0.7, 0.7, 7])
    with cols[0]:
        if st.button("Save", width="stretch"):
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

                upload_to_github(
                    file_path=f"recipes/{name.lower().replace(' ', '_')}.json",
                    content_string=json.dumps(recipe_data, indent=4)
                )

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

    with top_bar:
        with cols_top[0]:
            if st.session_state.get("just_random", False):
                st.success(f"🎉 Your random recipe for today: **{recipe_name}**")
                st.session_state["just_random"] = False

    # Display random recipe message if applicable
    # if st.session_state.get("just_random", False):
    #     st.success(f"🎉 Your random recipe for today: **{recipe_name}**")
    #     st.session_state["just_random"] = False

    st.title(recipe["name"])

    category = recipe.get("category", "N/A")
    duration = recipe.get("duration", "N/A")
    st.markdown(f"<div style='font-size:16px; color:gray;'>{category.capitalize()} | {duration} min</div>", unsafe_allow_html=True)

    # --- If flagged, leave edit mode after saving ---
    if st.session_state.get("leave_edit_mode", False):
        st.session_state.show_edit_recipe = False
        del st.session_state["leave_edit_mode"]

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

        # --- Buttons in one row: Save + Delete ---
        cols = st.columns([0.7, 0.7, 7])  # first two columns same size, third fills space

        with cols[0]:
            if st.button("Save", key=f"save_{recipe_name}", width="stretch"):
                # Validate inputs
                if not name.strip():
                    st.error("Recipe name required.")
                elif category == "":
                    st.error("Category required.")
                else:
                    old_file_path = os.path.join(RECIPE_DIR, f"{recipe_name.lower().replace(' ', '_')}.json")
                    new_file_path = os.path.join(RECIPE_DIR, f"{name.lower().replace(' ', '_')}.json")

                    updated_recipe = {
                        "name": name,
                        "category": category,
                        "duration": duration,
                        "ingredients": ingredients,
                        "instructions": instructions
                    }

                    with open(new_file_path, "w") as f:
                        json.dump(updated_recipe, f, indent=4)

                    upload_to_github(
                        file_path=f"recipes/{name.lower().replace(' ', '_')}.json",
                        content_string=json.dumps(updated_recipe, indent=4)
                    )

                    if old_file_path != new_file_path and os.path.exists(old_file_path):
                        os.remove(old_file_path)

                    st.success(f"Updated recipe: {name}")
                    st.session_state.selected_recipe = name
                    recipes = load_recipes()
                    st.session_state["leave_edit_mode"] = True
                    st.rerun()

        with cols[1]:
            if st.button("Delete", key=f"delete_{recipe_name}", width="stretch"):
                st.session_state.show_delete_confirm = True

        # --- Delete confirmation overlay ---
        if st.session_state.get("show_delete_confirm", False):
            st.warning(f"⚠️ Delete **{recipe_name}**? This cannot be undone.")

            confirm_cols = st.columns([0.7, 0.7, 7])
            with confirm_cols[0]:
                if st.button("Yes", key=f"confirm_delete_{recipe_name}", width="stretch"):
                    file_name = f"{recipe_name.lower().replace(' ', '_')}.json"

                    if delete_recipe(file_name):
                        # st.success(f"Deleted {recipe_name}")
                        st.session_state.selected_recipe = None
                        recipes = load_recipes()

                    delete_from_github(f"recipes/{file_name}")

                    # Hide overlay before rerun
                    st.session_state.show_delete_confirm = False
                    st.rerun()

            with confirm_cols[1]:
                if st.button("No", key=f"cancel_delete_{recipe_name}", width="stretch"):
                    # Hide overlay immediately
                    st.session_state.show_delete_confirm = False
                    st.rerun()  # or st.rerun() in latest Streamlit

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