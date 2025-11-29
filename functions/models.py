from firebase_admin import initialize_app, auth, firestore
from firebase_admin.firestore import Client
import uuid
from datetime import datetime, timezone

STATUSES = ["Pending", "In Progress", "Completed"]


# model class for epic
class Epic:
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        creator_id: str,
        status: str,
        child_user_stories: list = [],
        assigned_user_id: str = None,
        due_date: str = "",  # format: "YYYY-MM-DDTHH:MM:SS+00:00" (ISO 8601 with timezone)
        created_at: str = None,
    ):
        if status not in STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {STATUSES}")
        self.id = id
        self.name = name
        self.description = description
        self.creator_id = creator_id
        self.assigned_user_id = assigned_user_id
        self.child_user_stories = child_user_stories
        self.status = status
        if due_date != "":
            try:
                datetime.fromisoformat(due_date)
                self.due_date = due_date
            except ValueError:
                raise ValueError(
                    f"Invalid due_date format: {due_date}. Must be ISO 8601 format (YYYY-MM-DDTHH:MM:SS+00:00)"
                )
        else:
            self.due_date = ""
        self.created_at = (
            created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "creator_id": self.creator_id,
            "child_user_stories": self.child_user_stories,
            "assigned_user_id": self.assigned_user_id,
            "status": self.status,
            "due_date": self.due_date,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict, id: str = None):
        try:
            return Epic(
                id=id or uuid.uuid4().hex,
                name=data["name"],
                description=data["description"],
                creator_id=data["creator_id"],
                status=data["status"],
                assigned_user_id=data["assigned_user_id"],
                child_user_stories=data["child_user_stories"],
                due_date=data["due_date"],
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")

    @staticmethod
    def from_firestore(doc) -> "Epic":
        data = doc.to_dict()
        return Epic(
            id=doc.id,
            name=data["name"],
            description=data["description"],
            creator_id=data["creator_id"],
            status=data["status"],
            assigned_user_id=data["assigned_user_id"],
            child_user_stories=data["child_user_stories"],
            due_date=data["due_date"],
            created_at=data["created_at"],
        )

    @staticmethod
    def to_firestore(epic: "Epic", db: Client) -> dict:
        epic_ref = db.collection("epics").document(epic.id)
        epic_ref.set(epic.to_dict())
        return epic_ref


class Story:
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        status: str,
        creator_id: str,
        child_tasks: list = [],
        assigned_user_id: str = None,
        epic_id: str = None,
        due_date: str = None,
        created_at: str = None,
    ):
        if status not in STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {STATUSES}")
        self.id = id
        self.name = name
        self.description = description
        self.status = status
        self.epic_id = epic_id
        self.child_tasks = child_tasks
        self.creator_id = creator_id
        self.assigned_user_id = assigned_user_id
        if due_date is not None:
            try:
                datetime.fromisoformat(due_date)
                self.due_date = due_date
            except ValueError:
                raise ValueError(
                    f"Invalid due_date format: {due_date}. Must be ISO 8601 format (YYYY-MM-DDTHH:MM:SS+00:00)"
                )
        else:
            self.due_date = None
        self.created_at = (
            created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "epic_id": self.epic_id,
            "child_tasks": self.child_tasks,
            "creator_id": self.creator_id,
            "assigned_user_id": self.assigned_user_id,
            "due_date": self.due_date,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict, id: str = None):
        try:
            return Story(
                id=id or uuid.uuid4().hex,
                name=data["name"],
                description=data["description"],
                status=data["status"],
                epic_id=data["epic_id"],
                child_tasks=data["child_tasks"],
                creator_id=data["creator_id"],
                assigned_user_id=data["assigned_user_id"],
                due_date=data["due_date"],
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")

    @staticmethod
    def from_firestore(doc) -> "Story":
        data = doc.to_dict()
        return Story(
            id=doc.id,
            name=data["name"],
            description=data["description"],
            status=data["status"],
            epic_id=data["epic_id"],
            child_tasks=data["child_tasks"],
            creator_id=data["creator_id"],
            assigned_user_id=data["assigned_user_id"],
            due_date=data["due_date"],
            created_at=data["created_at"],
        )

    @staticmethod
    def to_firestore(story: "Story", db: Client) -> dict:
        story_ref = db.collection("stories").document(story.id)
        story_ref.set(story.to_dict())
        return story_ref


class Task:
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        status: str,
        creator_id: str,
        assigned_user_id: str = None,
        story_id: str = None,
        due_date: str = None,
        created_at: str = None,
    ):
        if status not in STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {STATUSES}")
        self.id = id
        self.creator_id = creator_id
        self.name = name
        self.description = description
        self.status = status
        self.story_id = story_id
        self.assigned_user_id = assigned_user_id
        if due_date is not None:
            try:
                datetime.fromisoformat(due_date)
                self.due_date = due_date
            except ValueError:
                raise ValueError(
                    f"Invalid due_date format: {due_date}. Must be ISO 8601 format (YYYY-MM-DDTHH:MM:SS+00:00)"
                )
        else:
            self.due_date = None
        self.created_at = (
            created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "story_id": self.story_id,
            "creator_id": self.creator_id,
            "assigned_user_id": self.assigned_user_id,
            "due_date": self.due_date,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict, id: str = None):
        try:
            task = Task(
                id=id or uuid.uuid4().hex,
                name=data["name"],
                description=data["description"],
                status=data["status"],
                story_id=data["story_id"],
                creator_id=data["creator_id"],
                assigned_user_id=data["assigned_user_id"],
                due_date=data["due_date"],
            )
            return task
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")

    @staticmethod
    def from_firestore(doc) -> "Task":
        data = doc.to_dict()
        return Task(
            id=doc.id,
            name=data["name"],
            description=data["description"],
            status=data["status"],
            story_id=data["story_id"],
            creator_id=data["creator_id"],
            assigned_user_id=data["assigned_user_id"],
            due_date=data["due_date"],
            created_at=data["created_at"],
        )

    @staticmethod
    def to_firestore(task: "Task", db: Client) -> dict:
        task_ref = db.collection("tasks").document(task.id)
        task_ref.set(task.to_dict())
        return task_ref
