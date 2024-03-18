from datetime import datetime, timedelta

from django.db.models import Count

from experiments import models as em
from prolific import models as pm
from prolific import outgoing_api as api

from django_q.tasks import schedule

"""
on add participant to studycollection:
    - create collection wide timer
        when hit if not all studies complete send message and set grace timer
    - create initial timer
        when hit message? or kick?

on battery completion:
    - create inter study min timer
        When hit add to next participant group
    - create inter study max timer
        when hit check to see if started:
            if not send message and set grace timer
"""


def on_add_to_collection(scs):
    if scs.failed_at:
        print("trying to add to failed SCS ${scs.id} ${scs.failed_at}")
        return
    sc = scs.study_collection
    ss = pm.objects.get(subject=scs.subject, study=sc.study_set.first())
    if (
        sc.time_to_start_first_study != None
        and sc.time_to_start_first_study > timedelta(0)
    ):
        schedule(
            "prolific.tasks.initial_warning",
            ss.id,
            next_run=datetime.now() + sc.time_to_start_first_study,
        )
    if (
        sc.collection_time_to_warning != None
        and sc.collection_time_to_warning > timedelta(0)
    ):
        schedule(
            "prolific.tasks.collection_warning",
            scs.id,
            next_run=datetime.now() + sc.collection_time_to_warning,
        )


def on_complete_battery(sc, current_study, subject_id):
    study = sc.next_study(current_study)
    delay = sc.inter_study_delay if sc.inter_study_delay != None else timedelta(0)
    ss = pm.StudySubject.objects.get(study=current_study, subject=subject_id)
    if ss.status == "kicked":
        return
    if ss.study_collection and ss.study_collection_subject.failed_at:
        return

    schedule(
        "prolific.tasks.end_study_delay",
        study.id,
        subject_id,
        next_run=datetime.now() + delay,
    )


"""
    This is the inter-study delay, we want subjects to wait before starting next study.
"""


def end_study_delay(study_id, subject_id):
    study = pm.Study.objects.get(id=study_id)
    subject = em.Subject.objects.get(id=subject_id)
    study_subject, created = pm.StudySubject.objects.get_or_create(
        study=study, subject=subject
    )
    sc = study.study_collection
    scs = pm.StudyCollectionSubject.objects.get(subject=subject, study_collection=sc)
    if scs.failed_at:
        return
    scs.current_study = study
    scs.save()
    study.add_to_allowlist([subject.prolific_id])

    if (
        sc.collection_time_to_warning != None
        and sc.study_collection.study_time_to_warning > timedelta(0)
    ):
        schedule(
            "prolific.tasks.study_warning",
            scs.id,
            study_id,
            next_run=datetime.now() + sc.study_collection.study_time_to_warning,
        )


"""
    Any study must be started within a certain amount of time.
"""


def study_warning(scs_id, study_id):
    scs = pm.StudyCollectionSubject.objects.get(id=scs_id)
    sc = scs.study_collection
    study = pm.Study.objects.get(id=study_id)
    started = (
        em.Assignment.objects.filter(alt_id=study.remote_id)
        .exclude(status="not-started")
        .count()
    )
    if not started:
        study_subject = pm.StudySubject.get(study=study, subject=scs.subject)
        api.send_message(
            scs.subject.prolific_id,
            study_id,
            sc.collection_warning_message,
        )
        study_subject.warned_at = datetime.now()
        study_subject.save()
        if sc.study_grace_interval != None and sc.study_grace_interval > timedelta(0):
            schedule(
                "prolific.tasks.study_end_grace",
                scs_id,
                study_id,
                next_run=datetime.now() + scs.study_collection.study_grace_interval,
            )


def study_end_grace(scs_id, study_id):
    scs = pm.StudyCollectionSubject.objects.get(id=scs_id)
    if scs.failed_at:
        return
    study = pm.Study.objects.get(id=study_id)
    started = (
        em.Assignment.objects.filter(subject=scs.subject, alt_id=study.remote_id)
        .exclude(status="not-started")
        .count()
    )
    if started:
        return f"{scs.subject} has started {study} taking no action"

    study_subject, created = pm.StudySubject.objects.get_or_create(
        study=study, subject=scs.subject
    )

    if scs.study_collection.study.kick_on_timeout:
        status = "kicked"
        study.remove_participant(scs.subject.prolific_id)
        message = f"removed ${scs.subject.prolific_id} from ${study} for not starting battery on time"
    else:
        status = "flagged"
        message = f"flagged ${scs.subject.prolific_id} from ${study} for not starting battery on time"

    study_subject.status = status
    study_subject.status_reason = "study-timer"
    scs.status = status
    scs.status_reason = "study-timer"
    study_subject.save()
    scs.save()


"""
    These are special for the first study a participant must start.
"""


def initial_warning(ss_id):
    ss = pm.StudySubject.objects.get(id=ss_id)
    if ss.study_collection_subject.failed_at:
        return
    if ss.assignment.status != "not-started":
        return f"{ss.subject} started {ss.study} before time to first study"
    api.send_message(
        ss.subject.prolific_id,
        ss.study.remote_id,
        ss.study.study_collection.collection_warning_message,
    )
    ss.warned_at = datetime.now()
    ss.save()
    schedule(
        "initial_end_grace",
        ss_id,
        next_run=datetime.now() + scs.study_collection.collection_grace_interval,
    )


def initial_end_grace(ss_id):
    ss = pm.StudySubject.objects.get(id=ss_id)
    if ss.study_collection_subject.failed_at:
        return

    if ss.assignment.status != "not-started":
        return f"{ss.subject} started {ss.study} before time to first study grace ended"
    api.send_message(
        scs.subject.prolific_id,
        first_study.remote_id,
        scs.study_collection.failure_to_start_message,
    )
    ss.study.remove_participant(ss.subject.prolific_id)
    ss.status = "kicked"
    ss.status_reason("initial-timer")
    ss.save()
    return f"removed {scs.subject.prolific_id} from {scs.study_collection}. Failed to start first battery on time"


"""
    There is an absolute max amount of time a subject can take to complete all studies.
"""


def collection_warning(scs_id):
    scs = pm.StudyCollectionSubject.objects.get(id=scs_id)
    if scs.failed_at:
        return
    batteries = em.Battery.objects.filter(
        study__study_collection__id=scs.study_collection.id
    )
    battery_pks = batteries.values("pk").annotate(count=Count("id"))
    studies = scs.study_collection.study_set.all().order_by("rank")
    assignments = em.Assignment.objects.filter(
        subject=scs.subject, battery__in=batteries
    )
    completed = assignments.filter(status="completed").count() == batteries.count()
    if not completed:
        if (
            scs.study_collection.collection_grace_interval != None
            and scs.study_collection.collection_grace_interval > timedelta(0)
        ):
            schedule(
                "prolific.tasks.collection_end_grace",
                f"{scs_id}",
                next_run=datetime.now()
                + scs.study_collection.collection_grace_interval,
            )
        # membership in first study is garunteed.
        if scs.current_study:
            study = scs.current_study
        else:
            study = scs.study_collection.study_set.first()
        api.send_message(
            scs.subject.prolific_id,
            first_study.id,
            scs.study_collection.collection_warning_message,
        )
        scs.warned_at = datetime.now()
        scs.save()


def collection_end_grace(scs_id):
    scs = pm.StudyCollectionSubject.objects.get(id=scs_id)
    if scs.failed_at:
        return
    batteries = em.Battery.objects.filter(
        study__study_collection__id=scs.study_collection.id
    )
    studies = scs.study_collection.study_set.all()
    assignments = em.Assignment.objects.filter(
        subject=scs.subject, battery__in=batteries
    )
    completed = assignments.filter(status="completed").count() == batteries.count()

    if not completed:
        if scs.study_collection.collection_kick_on_timeout:
            for study in scs.study_collection.study_set.all():
                study.remove_participant(pid=scs.subject.prolific_id)
            scs.status = "kicked"
            scs.status_reason = "collection-timer"
        else:
            scs.status = "flagged"
            scs.status_reason = "collection-timer"
        scs.save()
