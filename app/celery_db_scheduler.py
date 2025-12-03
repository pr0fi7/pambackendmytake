import json
from datetime import timedelta

from celery.beat import ScheduleEntry, Scheduler
from celery.schedules import crontab

from app.db.database import DatabaseConnector
from app.entities.workflows.workflow import Workflow, WorkflowSchedule
from app.models.workflows.workflow import WorkflowModel


class DatabaseScheduler(Scheduler):
    """Celery Beat Scheduler that loads schedules from the DB every tick."""

    max_interval = 60  # seconds, refresh every 1 min

    def setup_schedule(self):
        self._load_from_db()

    def _load_from_db(self):
        """Load all active workflows and update self.schedule"""
        self.schedule = {}

        with DatabaseConnector() as db:
            workflows = (
                db.session.query(Workflow)
                .filter(
                    Workflow.is_active,
                    Workflow.deleted_date.is_(None),
                )
                .all()
            )
            workflows = WorkflowModel.validate_list_model(workflows)

            for wf in workflows:
                cfg_raw = wf.run_options.model_dump() if wf.run_options else None
                cfg = json.loads(cfg_raw) if isinstance(cfg_raw, str) else cfg_raw
                if not cfg or cfg.get("run_variant") == "manual":
                    continue

                schedule_row = (
                    db.session.query(WorkflowSchedule)
                    .filter_by(workflow_id=wf.id)
                    .first()
                )
                celery_task_name = f"workflow_{wf.id}"

                if schedule_row:
                    schedule_row.repeat_every = cfg["repeat_every"]
                    schedule_row.hour = cfg.get("hour")
                    schedule_row.minute = cfg.get("minute")
                    schedule_row.week_day = cfg.get("week_day")
                    schedule_row.meridiem = cfg.get("meridiem")
                else:
                    schedule_row = WorkflowSchedule(
                        workflow_id=wf.id,
                        repeat_every=cfg["repeat_every"],
                        hour=cfg.get("hour"),
                        minute=cfg.get("minute"),
                        week_day=cfg.get("week_day"),
                        meridiem=cfg.get("meridiem"),
                    )
                    db.session.add(schedule_row)

                db.session.commit()

                schedule = self.convert_to_schedule(cfg)

                self.schedule[celery_task_name] = ScheduleEntry(
                    name=celery_task_name,
                    task="app.worker.execute_workflow",
                    schedule=schedule,
                    args=(str(wf.id),),
                    options={"queue": "celery"},
                )

            inactive_schedules = (
                db.session.query(WorkflowSchedule)
                .join(Workflow)
                .filter(Workflow.is_active.is_(False))
                .all()
            )
            for sched in inactive_schedules:
                celery_task_name = f"workflow_{sched.workflow_id}"
                if celery_task_name in self.schedule:
                    del self.schedule[celery_task_name]
                db.session.delete(sched)
            db.session.commit()

    @staticmethod
    def convert_to_schedule(cfg: dict):
        """Convert workflow config to Celery schedule (timedelta or crontab)."""
        repeat_every = cfg.get("repeat_every", "hour")
        hour = cfg.get("hour", 0)
        minute = cfg.get("minute", 0)
        meridiem = cfg.get("meridiem", "AM")

        if meridiem == "PM" and hour < 12:
            hour += 12
        elif meridiem == "AM" and hour == 12:
            hour = 0

        if repeat_every == "hour":
            return timedelta(hours=1)
            # return timedelta(minutes=1)
        elif repeat_every == "day":
            return crontab(hour=hour, minute=minute)
        elif repeat_every == "week":
            week_day = cfg.get("week_day", 1)
            return crontab(hour=hour, minute=minute, day_of_week=week_day - 1)
        else:
            return timedelta(hours=1)

    def tick(self):
        """Called every second by Celery Beat. Refresh DB schedules every tick."""
        self._load_from_db()
        return super().tick()
