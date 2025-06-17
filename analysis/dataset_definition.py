from ehrql import create_dataset, case, when, years, show
from ehrql.tables.tpp import patients, practice_registrations, clinical_events, addresses, apcs

import codelists


dataset = create_dataset()

### Note: can add parameterisation - i.e. to run code over range of different values (e.g. dates)


# Set desired size for dummy date (note - larger size means it will take longer to generate)
dataset.configure_dummy_data(population_size=100000)

# Set baseline date, and end of follow-up
#   can be same date for everyone, or patient specific
index_date = "2020-03-31"
end_date = "2024-12-31"

# Sex - possible values are male, female, intersex
#   to avoid disclosure due to small number of intersex people,
#   only male / female sex should be included if stratifying by sex
dataset.sex = patients.sex

# Age - note that DOB is always first of month;
#   due to risk of incorrectly recorded age / DOB for the very old,
#   exclude people >115 years
dataset.dob = patients.date_of_birth

# DOD from primary care - cause of death is in ONS
dataset.dod = patients.date_of_death

# GP practice registration 
has_registration = practice_registrations.for_patient_on(
    index_date
).exists_for_patient()

# Practice registrations spanning study period
registrations = practice_registrations.spanning(
        index_date, end_date
    )

# Earliest registration start date
dataset.practice_reg_start_date = registrations.sort_by(
        practice_registrations.start_date
    ).first_for_patient().start_date

# Latest registration end date (if they did not deregister will be null)
dataset.practice_reg_end_date = registrations.sort_by(
       practice_registrations.end_date
    ).last_for_patient().end_date


# IMD decile of patient address
imd = addresses.for_patient_on(index_date).imd_rounded
dataset.imd10 = case(
        when((imd >= 0) & (imd < int(32844 * 1 / 10))).then("1 (most deprived)"),
        when(imd < int(32844 * 2 / 10)).then("2"),
        when(imd < int(32844 * 3 / 10)).then("3"),
        when(imd < int(32844 * 4 / 10)).then("4"),
        when(imd < int(32844 * 5 / 10)).then("5"),
        when(imd < int(32844 * 6 / 10)).then("6"),
        when(imd < int(32844 * 7 / 10)).then("7"),
        when(imd < int(32844 * 8 / 10)).then("8"),
        when(imd < int(32844 * 9 / 10)).then("9"),
        when(imd >= int(32844 * 9 / 10)).then("10 (least deprived)"),
        otherwise="unknown"
)

# Ethnicity recording care vary - so extract must recent recorded ethnicity prior 
#   to date of interest - but note that sometimes ethnicity is given a random date (1900-01-01),
#   rather than the actual date of recording
# For more info on ethnicity recording in OpenSAFLEY see: Andrews et al. 10.1186/s12916-024-03499-5 

# Ethnicity with 6 categories
# First, find most recent recorded ethnicity
ethnicity6 = clinical_events.where(
        clinical_events.snomedct_code.is_in(codelists.ethnicity_codes_6)
    ).where(
        clinical_events.date.is_on_or_before("2022-04-01")
    ).sort_by(
        clinical_events.date
    ).last_for_patient().snomedct_code.to_category(codelists.ethnicity_codes_6)

# Save to dataset with labels
dataset.ethnicity6 = case(
    when(ethnicity6 == "1").then("White"),
    when(ethnicity6 == "2").then("Mixed"),
    when(ethnicity6 == "3").then("South Asian"),
    when(ethnicity6 == "4").then("Black"),
    when(ethnicity6 == "5").then("Other"),
    when(ethnicity6 == "6").then("Not stated"),
    otherwise="Unknown"
)

# Ethnicity with 16 categories
# First, find most recent recorded ethnicity
ethnicity16 = clinical_events.where(
        clinical_events.snomedct_code.is_in(codelists.ethnicity_codes_16)
    ).where(
        clinical_events.date.is_on_or_before(index_date)
    ).sort_by(
        clinical_events.date
    ).last_for_patient().snomedct_code.to_category(codelists.ethnicity_codes_16)

# Save to dataset with labels
dataset.ethnicity16 = case(
    when(ethnicity16 == "1").then("White - British"),
    when(ethnicity16 == "2").then("White - Irish"),
    when(ethnicity16 == "3").then("White - Other"),
    when(ethnicity16 == "4").then("Mixed - White/Black Caribbean"),
    when(ethnicity16 == "5").then("Mixed - White/Black African"),
    when(ethnicity16 == "6").then("Mixed - White/Asian"),
    when(ethnicity16 == "7").then("Mixed - Other"),
    when(ethnicity16 == "8").then("Asian or Asian British - Indian"),
    when(ethnicity16 == "9").then("Asian or Asian British - Pakistani"),
    when(ethnicity16 == "10").then("Asian or Asian British - Bangladeshi"),
    when(ethnicity16 == "11").then("Asian or Asian British - Other"),
    when(ethnicity16 == "12").then("Black - Caribbean"),    
    when(ethnicity16 == "13").then("Black - African"),
    when(ethnicity16 == "14").then("Black - Other"),
    when(ethnicity16 == "15").then("Other - Chinese"),
    when(ethnicity16 == "16").then("Other - Other"),
    otherwise="Unknown"
)

# Region of GP practice - care must be taken when interpreting region data,
#   as distribution of TPP practices within regions is not random
dataset.region = practice_registrations.for_patient_on(index_date).practice_nuts1_region_name

# This is who we want included in the initial dataset
# Note - age / sex are rarely missing - if missing, it is usually a sign of poor data quality
#   so exclude
dataset.define_population(
    has_registration # registered with TPP practice
    & ((dataset.dod < index_date) | dataset.dod.is_null()) # still alive on index date
    & dataset.dob.is_not_null() # non missing age
    & dataset.sex.is_in(["male","female"]) # non missing sex
    )


############################

# Create temporary subset of datasets to cut down processing time

# Extract all primary care events before index date
primary_events_2yrs = clinical_events.where(
    clinical_events.date.is_on_or_between(index_date - years(2), index_date)
)

# Extract all secondary care events before index date
secondary_events_2yrs = apcs.where(
    apcs.admission_date.is_on_or_between(index_date - years(2), index_date)
)


# Diabetes in primary care
diabetes_date = primary_events_2yrs.where(
        primary_events_2yrs.snomedct_code.is_in(codelists.diabetes_codes)
    ).sort_by(
        primary_events_2yrs.date
    ).last_for_patient().date

# Diabetes in primary care resolved
diabetes_resolved_date = primary_events_2yrs.where(
        primary_events_2yrs.snomedct_code.is_in(codelists.diabetes_resolved_codes)
    ).sort_by(
        primary_events_2yrs.date
    ).last_for_patient().date

# Does patient have diabetes recorded in primary care -
#   patient has a diabetes diagnosis, with either no
#   diabetes resolved diagnosis following the diabetes diagnosis
dataset.diabetes_primary = (
    diabetes_date.is_not_null()
    & (diabetes_resolved_date.is_null() | (diabetes_resolved_date < diabetes_date))
)

# Diabetes in secondary care (primary diagnosis only)
dataset.diabetes_secondary = secondary_events_2yrs.where(
        secondary_events_2yrs.primary_diagnosis.is_in(codelists.diabetes_secondary_codes)
).exists_for_patient()
    

# Example code to extract range of comorbidities 
# comorb_codes = {
#     "diabetes": codelists.diabetes_codes,
#     "cardiac": codelists.cardiac_codes,
#     "copd": codelists.copd_codes,
#     "liver": codelists.liver_codes,
#     "ckd": codelists.ckd_codes,
#     "oa": codelists.osteoarthritis_codes,
#     "ra": codelists.ra_codes,
#     "depression": codelists.depression_codes,
#     "anxiety": codelists.anxiety_codes,
#     "smi": codelists.smi_codes,
#     "oud": codelists.oud_codes
#     }

# for comorb, comorb_codelist in comorb_codes.items():

#     snomed_query = primary_events_2yrs.where(
#             primary_events_2yrs.snomedct_code.is_in(comorb_codelist)
#         ).exists_for_patient()
    
#     dataset.add_column(comorb, snomed_query)

