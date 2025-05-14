import pandas as pd
import json

def get_location_details(location=None, category=None, cap=None, cap_min=None, cap_max=None):
    try:
        # Load CSV
        csv_file = "Location_Category.csv"
        df = pd.read_csv(csv_file)

        # Ensure required columns exist
        required_columns = {"Location", "revised proposed cat", "Revised Cap in cr"}
        if not required_columns.issubset(df.columns):
            raise ValueError("CSV file is missing one or more required columns.")

        # Standardize column names
        df = df.rename(columns={"revised proposed cat": "proposed cat", "Revised Cap in cr": "Cap in cr"})

        # Convert "Cap in cr" to numeric
        df["Cap in cr"] = pd.to_numeric(df["Cap in cr"], errors='coerce')

        # Apply filters
        filtered_df = df.copy()

        if location:
            filtered_df = filtered_df[filtered_df["Location"].str.lower() == location.lower()]
        if category:
            filtered_df = filtered_df[filtered_df["proposed cat"].str.lower() == category.lower()]
        if cap is not None:
            filtered_df = filtered_df[filtered_df["Cap in cr"] == cap]
        else:
            if cap_min is not None:
                filtered_df = filtered_df[filtered_df["Cap in cr"] >= cap_min]
            if cap_max is not None:
                filtered_df = filtered_df[filtered_df["Cap in cr"] <= cap_max]

        # If no filters or no matches, return full data
        if (location is None and category is None and cap is None and cap_min is None and cap_max is None) or filtered_df.empty:
            return df[["Location", "proposed cat", "Cap in cr"]].to_json(orient="records")
        else:
            return filtered_df[["Location", "proposed cat", "Cap in cr"]].to_json(orient="records")

    except Exception as e:
        return filtered_df[["Location", "proposed cat", "Cap in cr"]].to_json(orient="records")


# Single cap value
# print(get_location_details(cap=0.5))

# Range
# print(get_location_details(cap_min=0.75, cap_max=1))

# Location + category + single cap
# print(get_location_details(location="Chennai"))

# No filters
# print(get_location_details())