import operator
from functools import reduce # for function building, e.g. any_of
from ehrql.tables.tpp import (
    apcs, 
    clinical_events, 
    medications, 
    ons_deaths,
    emergency_care_attendances as eca
)


def ed_attendances(start_date, end_date, where=True):
    return (
        eca.where(where)
        .where(eca.arrival_date.is_on_or_between(start_date, end_date))
        .count_for_patient()
    )

def primary_care_attendances(start_date, end_date, where=True):
    return (
        clinical_events.where(where)
        .where(clinical_events.date.is_on_or_between(start_date, end_date))
        .count_for_patient()
    )


def hospital_admissions(start_date, end_date, where=True):
    return (
        apcs.where(where)
        .where(apcs.admission_date.is_on_or_between(start_date, end_date))
        .count_for_patient()
    )
