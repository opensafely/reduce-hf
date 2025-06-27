from ehrql import (
    create_dataset, 
    case, 
    when, 
    years,
    days,
    show,
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
)

dataset = create_dataset()

dataset.configure_dummy_data(population_size=1000)

#using these dates for now
project_index_date = '2017-01-01'
end_date = '2025-01-01'


#registered for at least 1 year
#practice registration at minimum study end date - 1 year
#exclude historic registrations that ended before project_index_date

has_registration = practice_registrations.where(
    practice_registrations.start_date <= end_date - years(1)
    ).except_where(
    practice_registrations.end_date < project_index_date
    ).exists_for_patient()


#define population (inclusion/exclusion criteria)

dataset.define_population(
    has_registration 
    & patients.sex.is_in(['male','female']) #known sex proxy for data quality
    & patients.date_of_birth.is_not_null() #known dob proxy for data quality
    & ~(patients.age_on(end_date) < 45) #remove pts < 45
    & ~(patients.age_on(project_index_date) >= 110) #remove pts age 110+ 
    & (patients.is_alive_on(project_index_date)) #remove pts who died before start
   )

#add demograhpics

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


#add health service use. Date should be date of HF diagnosis. 

time_periods = {
    '3m': days(90),
    '6m': days(180),
    '12m': days(360)
}

for time_name, time in time_periods.items():

    dataset.add_column('ed_attendances_'+time_name, ed_attendances(project_index_date, project_index_date + time))
    dataset.add_column('primary_care_attendances_'+time_name, primary_care_attendances(project_index_date, project_index_date + time))
    dataset.add_column('hospital_admissions_'+time_name, hospital_admissions(project_index_date, project_index_date + time))





