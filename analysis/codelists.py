###############################################################################
# To add codelists to project:
# - find pre-existing codelist, or create new codelist on OpenCodelists 
# - add codelist to codelists/codelists.txt in GitHub repository
# - run "opensafely codelists update" in terminal in Codespaces - 
#       this will automatically add codelist csv to codelists folder
# - use codelist_from_csv to call up codelists (see below) - 
#       either in a separate python file like this one - or elsewhere
###############################################################################


## Import code building blocks from cohort extractor package
from ehrql import codelist_from_csv
 
## Type 2 diabetes - primary care
diabetes_codes = codelist_from_csv(
  "codelists/nhsd-primary-care-domain-refsets-dm_cod.csv", 
  column = "code",
)

## Type 2 diabetes resolved - primary care
diabetes_resolved_codes = codelist_from_csv(
  "codelists/nhsd-primary-care-domain-refsets-dmres_cod.csv", 
  column = "code",
)

## Type 2 diabetes - secondary care
diabetes_secondary_codes = codelist_from_csv(
    "codelists/user-anschaf-type-2-diabetes-secondary-care.csv",
    column = "code"
)

## Ethnicity - 16 categories
ethnicity_codes_16 = codelist_from_csv(
    "codelists/opensafely-ethnicity-snomed-0removed.csv",
    column="snomedcode",
    category_column="Grouping_16",
)

## Ethnicity - 6 categories
ethnicity_codes_6 = codelist_from_csv(
    "codelists/opensafely-ethnicity-snomed-0removed.csv",
    column="snomedcode",
    category_column="Grouping_6",
)