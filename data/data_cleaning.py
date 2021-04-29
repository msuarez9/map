import pandas as pd
from datetime import datetime, timedelta, date
import numpy as np
import json

from scripts.calculate import calculate_age


def clean_api_code():

    # Survey and Environmental Data Import

    with open("data/SurveyDataMarch3.json", encoding="utf8") as file:
        data = json.load(file)
    survey_df = pd.json_normalize(data["results"])

    with open("data/HistoryEnvironmentalHealthMarch3.json", encoding="utf8") as file:
        data = json.load(file)
    environmental_df = pd.json_normalize(data["results"])

    # Clean Survey Data

    """
    Clean
    """
    survey_df = survey_df[
        [
            "objectId",
            "fname",
            "lname",
            "nickname",
            "relationship",
            "sex",
            "dob",
            "telephoneNumber",
            "educationLevel",
            "occupation",
            "communityname",
            "city",
            "province",
            "insuranceNumber",
            "insuranceProvider",
            "clinicProvider",
            "cedulaNumber",
            "surveyingUser",
            "surveyingOrganization",
            "latitude",
            "longitude",
            "createdAt",
            "updatedAt",
        ]
    ]

    """
    ReClean NaNs
    """
    survey_df = survey_df.replace({np.nan: ""})

    """
    Age Manipulation
    """
    survey_df["age"] = survey_df["dob"].apply(calculate_age)

    survey_df["relationship"] = survey_df["relationship"].replace("null, null", "")

    """
    ReClean NaNs
    """
    survey_df = survey_df.replace({np.nan: ""})

    # df_json = df.to_json(orient='records')
    df_dict = survey_df.to_dict("records")

    # Clean Environmental
    environmental_df = environmental_df.replace({np.nan: ""})
    environmental_df = environmental_df.drop_duplicates(subset=["client.objectId"])

    # Clean more
    survey_df_nulls = survey_df.replace({"": np.nan})
    environmental_df_nulls = environmental_df.replace({"": np.nan})

    # Cleaning the Data
    ## Fix typos, create new classifications

    # Replace mispelled/repeated values

    # Replace 'widow\n' with 'widow'
    survey_df = survey_df.replace("widow\n", "widow", regex=True)

    # Replace 'breastancler' with 'breastcancer'
    survey_df = survey_df.replace("breastcancler", "breastcancer", regex=True)

    # Replace 'lessThanprimary\n' with 'lessThanprimary'
    survey_df = survey_df.replace("lessThanprimary\n", "lessThanprimary", regex=True)

    # Replace 'moreThan10\n' with 'moreThan10'
    survey_df = survey_df.replace("moreThan10\n", "moreThan10", regex=True)

    # Replace underscores with hyphens for time ranges
    environmental_df = environmental_df.replace("1_2", "1-2", regex=True)
    environmental_df = environmental_df.replace("3_4", "3-4", regex=True)
    environmental_df = environmental_df.replace("5_10", "5-10", regex=True)

    # Re-classify flooring conditions
    # dirtPoor = poor, cementPoor/dirtWorking = working, cementWorking =good

    # flooring_options = ['poor','working','great']

    environmental_df = environmental_df.replace("dirtPoor", "poor", regex=True)
    environmental_df = environmental_df.replace("cementPoor", "working", regex=True)
    environmental_df = environmental_df.replace("dirtWorking", "working", regex=True)
    environmental_df = environmental_df.replace("cementWorking", "good", regex=True)

    # Re-classify roofing conditions
    # bad = poor, normal = working

    roofing_options = [
        "poor",
        "working",
        "great",
    ]  # Currently not an option for great. Crismary said that ideally these three categories would be beneficial

    environmental_df = environmental_df.replace("bad", "poor", regex=True)
    environmental_df = environmental_df.replace("normal", "working", regex=True)

    # Clean numberofIndividualsLivingintheHouse

    # Make all lowercase
    environmental_df["numberofIndividualsLivingintheHouse"] = environmental_df[
        "numberofIndividualsLivingintheHouse"
    ].str.lower()

    # Extract only numbers
    environmental_df[
        "numberofIndividualsLivingintheHouseDigits"
    ] = environmental_df.numberofIndividualsLivingintheHouse.str.extract("(\d+)")

    # Merge Columns
    environmental_df.loc[
        environmental_df["numberofIndividualsLivingintheHouseDigits"].isnull(),
        "numberofIndividualsLivingintheHouseDigits",
    ] = environmental_df["numberofIndividualsLivingintheHouse"]

    # Number spellings
    one_spellings = ["una", "uno"]
    two_spellings = ["dos"]
    three_spellings = ["tres", "trres"]
    four_spellings = ["cuatro", "cuatros"]

    for one in one_spellings:
        environmental_df.loc[
            environmental_df["numberofIndividualsLivingintheHouseDigits"].str.contains(
                one
            ),
            "numberofIndividualsLivingintheHouseDigits",
        ] = "1"
    for two in two_spellings:
        environmental_df.loc[
            environmental_df["numberofIndividualsLivingintheHouseDigits"].str.contains(
                two
            ),
            "numberofIndividualsLivingintheHouseDigits",
        ] = "2"
    for three in three_spellings:
        environmental_df.loc[
            environmental_df["numberofIndividualsLivingintheHouseDigits"].str.contains(
                three
            ),
            "numberofIndividualsLivingintheHouseDigits",
        ] = "3"
    for four in four_spellings:
        environmental_df.loc[
            environmental_df["numberofIndividualsLivingintheHouseDigits"].str.contains(
                four
            ),
            "numberofIndividualsLivingintheHouseDigits",
        ] = "4"

    # Final clean to ensure just number results
    environmental_df["numberofIndividualsLivingintheHouseDigits"] = environmental_df[
        "numberofIndividualsLivingintheHouseDigits"
    ].str.extract("(^(0|[1-9][0-9]{0,1})$)", expand=False)

    # Filter to remove leading 0s
    environmental_df["numberofIndividualsLivingintheHouseDigits"] = environmental_df[
        "numberofIndividualsLivingintheHouseDigits"
    ].astype(float)

    # Filter to remove non-possible values
    environmental_df.loc[
        (environmental_df.numberofIndividualsLivingintheHouseDigits > 20),
        "numberofIndividualsLivingintheHouseDigits",
    ] = np.nan

    # Clean City Names

    import difflib

    def f(x):
        try:
            return difflib.get_close_matches(x["city"], city_names)[0]
        except:
            return ""

    # Cities Identified
    city_names = [
        "tireo",
        "spm",
        "adansi",
        "consuelo",
        "constanza",
        "la romana",
        "ciudad de dios",
        "la vega",
        "santo domingo",
        "asokwa",
        "santiago",
        "santa fe",
        "san pedro de macorís",
        "el seibo",
    ]

    # Make all lowercase
    survey_df["city"] = survey_df["city"].str.lower()

    # # Apply function
    # survey_df["city_match"] = survey_df.apply(f, axis=1)
    # survey_df["city_match"] = survey_df["city_match"].replace(
    #     "spm", "San Pedro de Macorís", regex=True
    # )

    # Finding city names for the list
    # pd.set_option('display.max_rows', 400)
    # city_names = survey_df['city'].value_counts().to_frame()

    # Do better city mapping based on Scott City names Excel sheet

    # Environmental to clean

    # numberofChildrenLivinginHouseUndertheAgeof5
    # valuable to clean?

    # houseownership
    environmental_df["houseownership"] = environmental_df["houseownership"].replace(
        "owned", "Y", regex=True
    )
    environmental_df["houseownership"] = environmental_df["houseownership"].replace(
        "rented", "N", regex=True
    )

    # latrineAccess and clinicAccess and bathroomAccess
    environmental_df = environmental_df.replace("No", "N", regex=True)
    environmental_df = environmental_df.replace("Yes", "Y", regex=True)

    # Survey to clean
    # sex
    survey_df["sex"] = survey_df["sex"].str.lower()

    # city

    # dob and age (some are negative or too big)
    dob_max = datetime.today().date()
    dob_min = dob_max.replace(year=dob_max.year - 115)

    # Compare dob to see what is feasible, but first need to convert survey_df['dob'] to a datetime
    # pd.to_datetime(survey_df['dob'])
    # survey_df[survey_df['dob'] > dob_max] = ''
    # survey_df[survey_df['dob'] < dob_min] = ''

    survey_df[pd.to_numeric(survey_df["age"]) < 0] = ""
    survey_df[pd.to_numeric(survey_df["age"]) > 110] = ""

    # Join Data

    # Create merged data

    full_df = pd.merge(
        survey_df,
        environmental_df,
        left_on=["objectId"],
        right_on=["client.objectId"],
        how="right",
    )

    full_df = full_df.drop_duplicates(subset=["client.objectId"])
    full_df = full_df.drop(columns=["client.objectId", "objectId_y"])
    full_df = full_df.rename(columns={"objectId_x": "objectId"})
    full_df = full_df.replace({np.nan: ""})

    df = full_df

    # Create new columns for latrine or bathroom access

    df.loc[
        (df["latrineAccess"] == "Y") | (df["bathroomAccess"] == "Y"),
        "Latrine or Bathroom Access",
    ] = "Y"
    df.loc[
        (df["latrineAccess"] == "N") & (df["bathroomAccess"] == "N"),
        "Latrine or Bathroom Access",
    ] = "N"

    # Change numbers to digits without decimals
    import math

    # Age

    df["age"] = df["age"].replace("", np.nan)
    df["age"] = df["age"].astype("float").astype("Int64")

    # Individuals living in the hosue

    # df["numberofIndividualsLivingintheHouseDigits"] = df[
    #     "numberofIndividualsLivingintheHouseDigits"
    # ].replace("", np.nan)
    # df["numberofIndividualsLivingintheHouseDigits"] = (
    #     df["numberofIndividualsLivingintheHouseDigits"]
    #     .astype(str)
    #     .astype("float")
    #     .astype("Int64")
    # )

    # Relabeing values in df

    educationLevel_vals = [
        "",
        "lessThanprimary",
        "primary",
        "college",
        "highschool",
        "someHighSchool",
        "someCollege",
    ]
    educationLevel_vals_new = [
        "",
        "Less Than Primary School",
        "Completed Primary School",
        "Completed College",
        "Completed High School",
        "Some High School",
        "Some College",
    ]

    waterAccess_vals = [
        "",
        "2-3AWeek",
        "4-6AWeek",
        "1AMonth",
        "Never",
        "1AWeek",
        "everyday",
    ]
    waterAccess_vals_new = [
        "",
        "2-3x A Week",
        "4-6x A Week",
        "1x A Month",
        "Never",
        "1x A Week",
        "Every day",
    ]

    conditionoFloorinyourhouse_vals = ["", "good", "poor", "working"]
    conditionoFloorinyourhouse_vals_new = [
        "",
        "Great",
        "Needs Repair",
        "Adequate",
    ]  # reconsider great

    conditionoRoofinyourhouse_vals = ["", "working", "poor"]
    conditionoRoofinyourhouse_vals_new = ["", "Adequate", "Needs Repair"]

    stoveType_vals = [
        "",
        "stoveTop",
        "cementStove-Ventilation",
        "openfire-noVentilation",
    ]
    stoveType_vals_new = [
        "",
        "stoveTop",
        "Yes - Cement Stove",
        "No - Open Fire",
    ]  # talk about how to change values in future

    houseMaterial_vals = [
        "",
        "block",
        "wood",
        "partBlock_partWood",
        "zinc",
        "brick",
        "other",
        "clay",
    ]
    houseMaterial_vals_new = [
        "",
        "Block",
        "Wood",
        "Mix with Block and Wood",
        "Zinc",
        "Brick",
        "Other",
        "Clay",
    ]

    electricityAccess_vals = ["", "sometimes", "always", "never"]
    electricityAccess_vals_new = ["", "Sometimes", "Always", "Never"]

    foodSecurity_vals = ["", "not_sure", "N", "Y"]
    foodSecurity_vals_new = ["", "Uncertain", "No", "Yes"]

    govAssistance_vals = ["", "aprendiendo", "solidaridad", "other", "no_assistance"]
    govAssistance_vals_new = ["", "Learning", "Solidarity", "Other", "No Assistance"]

    all_vals = [
        educationLevel_vals,
        waterAccess_vals,
        conditionoFloorinyourhouse_vals,
        conditionoRoofinyourhouse_vals,
        stoveType_vals,
        houseMaterial_vals,
        electricityAccess_vals,
        foodSecurity_vals,
        govAssistance_vals,
    ]
    all_vals_new = [
        educationLevel_vals_new,
        waterAccess_vals_new,
        conditionoFloorinyourhouse_vals_new,
        conditionoRoofinyourhouse_vals_new,
        stoveType_vals_new,
        houseMaterial_vals_new,
        electricityAccess_vals_new,
        foodSecurity_vals_new,
        govAssistance_vals_new,
    ]

    # Rename values in columns for mapping

    # Relevant columns
    map_columns_tochange = [
        "educationLevel",
        "waterAccess",
        "conditionoFloorinyourhouse",
        "conditionoRoofinyourhouse",
        "stoveType",
        "houseMaterial",
        "electricityAccess",
        "foodSecurity",
        "govAssistance",
    ]

    for i in np.arange(len(map_columns_tochange)):
        for x in np.arange(len(all_vals)):
            for x_len in np.arange(len(all_vals[x])):
                df[map_columns_tochange[i]] = df[map_columns_tochange[i]].replace(
                    all_vals[x][x_len], all_vals_new[x][x_len]
                )

    # Rename columnn names for mapping. Also Filter out to only include necessary columns

    map_columns = [
        "objectId",
        "educationLevel",
        "latitude",
        "longitude",
        "age",
        "communityname",
        "city",
        "waterAccess",
        "clinicAccess",
        "conditionoFloorinyourhouse",
        "conditionoRoofinyourhouse",
        "stoveType",
        "houseMaterial",
        "electricityAccess",
        "foodSecurity",
        "govAssistance",
        "Latrine or Bathroom Access",
    ]

    rename_columns = [
        "objectId",
        "Education Level",
        "Latitude",
        "Longitude",
        "Age",
        "Community",
        "City",
        "Water Access",
        "Clinic Access",
        "Floor Condition",
        "Roof Condition",
        "Stove Ventilation",
        "House Material",
        "Electricity Access",
        "Food Security",
        "Government Assistance",
        "Latrine or Bathroom Access",
    ]

    df = df[df.columns[df.columns.isin(map_columns)]]
    for i in np.arange(len(map_columns)):
        df = df.rename(columns={map_columns[i]: rename_columns[i]})

    # Calculate Missings

    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

    return df
