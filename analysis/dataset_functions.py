#this script contains functions to add variables to dataset
#variables are grouped by type, and whether they are WP specific

from ehrql import (
    case,
    when,
    years,
    days,
    maximum_of,
)

from ehrql.tables.tpp import (
    patients,
    practice_registrations,
    clinical_events,
    addresses,
    apcs
)

from helper_functions import (
    ed_attendances,
    primary_care_attendances,
    hospital_admissions,
    first_matching_event_clinical_ctv3_before,
    first_matching_event_clinical_snomed_before,
    last_matching_event_clinical_snomed_before,
)

from codelists import *

def add_core(dataset, project_index_date):


    '''
    core variables don't differ between WPs
    they depend on project_index_date only

    parameters:

    dataset: dataset object initialised using create_dataset()
    project_index_date: for our project, 01-01-2017

    '''


    dataset.sex = patients.sex
    dataset.dob = patients.date_of_birth

    #add practice details
    # most recent prectice registration

    practice = practice_registrations.sort_by(
        practice_registrations.start_date,
        practice_registrations.end_date,
        practice_registrations.practice_pseudo_id).last_for_patient()

    dataset.practice_id = practice.practice_pseudo_id
    dataset.practice_registration_date = practice.start_date
    dataset.practice_deregistration_date = practice.end_date

    #patient index date latest of:
    # - project start
    # - practice registration - 1 year (to allow for coding of variables)
    # - 45th birthday

    dataset.patient_index = maximum_of(project_index_date,
        dataset.practice_registration_date - years(1),
        dataset.dob + years(45))

    #add area level details

    dataset.practice_stp = practice.practice_stp
    dataset.region = practice.practice_nuts1_region_name

    imd = addresses.for_patient_on(project_index_date).imd_rounded
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

    return dataset


def add_healthservice_use(dataset, index_date):


    '''
    add variables measuring health service use
    only needed for WP3 (?)

    '''

    time_periods = {
        '3m': days(90),
        '6m': days(180),
        '12m': days(360),
        '24m': years(2)
    }

    for time_name, time in time_periods.items():

        #use in time period before index_date
        dataset.add_column('ed_attendances_'+time_name, ed_attendances(index_date, index_date + time))
        dataset.add_column('primary_care_attendances_'+time_name, primary_care_attendances(index_date, index_date + time))
        dataset.add_column('hospital_admissions_'+time_name, hospital_admissions(index_date, index_date + time))

        #use in time period after index_date
        dataset.add_column('ed_attendances_pre_'+time_name, ed_attendances(index_date - time, index_date))
        dataset.add_column('primary_care_attendances_pre_'+time_name, primary_care_attendances(index_date - time, index_date))
        dataset.add_column('hospital_admissions_pre_'+time_name, hospital_admissions(index_date-time, index_date))

    return dataset


def add_comorbidities(dataset, index_date):

    '''
    add comorbidities. using index_date as a parameter
    means we can derive as binary variables rather than dates
    '''

    dataset.copd_date = first_matching_event_clinical_ctv3_before(
        copd_ctv3, index_date
        ).exists_for_patient()

    dataset.ckd_date = first_matching_event_clinical_snomed_before(
        ckd_snomed, index_date
        ).exists_for_patient()

    dataset.diabetes_date = first_matching_event_clinical_snomed_before(
        diabetes_snomed, index_date
        ).exists_for_patient()

    #using latest date for obesity, hypertension, and total cholesterol
    dataset.obesity_date = last_matching_event_clinical_snomed_before(
        bmi_obesity_snomed, index_date
        ).exists_for_patient()

    dataset.hypertension_date = last_matching_event_clinical_snomed_before(
        hypertension_snomed, index_date
        ).exists_for_patient()

    dataset.last_cholesterol_date = last_matching_event_clinical_snomed_before(
        cholesterol_snomed, index_date
        ).date

    return dataset
