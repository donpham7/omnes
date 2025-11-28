from firebase_admin import initialize_app, auth, firestore
from firebase_admin.firestore import Client
import uuid

STATUSES = ["Pending", "In Progress", "Completed"]


# model class for epic
class Epic:
    def __init__(
        self,
        epic_id: str,
        name: str,
        description: str,
        creator_id: str,
        status: str,
        child_user_stories: list = [],
        assigned_user_id: str = None,
    ):
        if status not in STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {STATUSES}")
        self.epic_id = epic_id
        self.name = name
        self.description = description
        self.creator_id = creator_id
        self.assigned_user_id = assigned_user_id
        self.child_user_stories = child_user_stories
        self.status = status

    def to_dict(self) -> dict:
        return {
            "epic_id": self.epic_id,
            "name": self.name,
            "description": self.description,
            "creator_id": self.creator_id,
            "child_user_stories": self.child_user_stories,
            "assigned_user_id": self.assigned_user_id,
            "status": self.status,
        }

    @staticmethod
    def from_dict(data: dict, id: str = None):
        try:
            return Epic(
                epic_id=id or uuid.uuid4().hex,
                name=data["name"],
                description=data["description"],
                creator_id=data["creator_id"],
                status=data["status"],
                assigned_user_id=data["assigned_user_id"],
                child_user_stories=data["child_user_stories"],
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")

    @staticmethod
    def from_firestore(doc) -> "Epic":
        data = doc.to_dict()
        return Epic(
            epic_id=doc.id,
            name=data["name"],
            description=data["description"],
            creator_id=data["creator_id"],
            status=data["status"],
            assigned_user_id=data["assigned_user_id"],
            child_user_stories=data["child_user_stories"],
        )

    @staticmethod
    def to_firestore(epic: "Epic", db: Client) -> dict:
        epic_ref = db.collection("epics").document(epic.epic_id)
        epic_ref.set(epic.to_dict())
        return epic_ref


class Story:
    def __init__(
        self,
        story_id: str,
        name: str,
        description: str,
        status: str,
        creator_id: str,
        child_tasks: list = [],
        assigned_user_id: str = None,
        epic_id: str = None,
    ):
        if status not in STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {STATUSES}")
        self.story_id = story_id
        self.name = name
        self.description = description
        self.status = status
        self.epic_id = epic_id
        self.child_tasks = child_tasks
        self.creator_id = creator_id
        self.assigned_user_id = assigned_user_id

    def to_dict(self) -> dict:
        return {
            "story_id": self.story_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "epic_id": self.epic_id,
            "child_tasks": self.child_tasks,
            "creator_id": self.creator_id,
            "assigned_user_id": self.assigned_user_id,
        }

    @staticmethod
    def from_dict(data: dict, id: str = None):
        try:
            return Story(
                story_id=id or uuid.uuid4().hex,
                name=data["name"],
                description=data["description"],
                status=data["status"],
                epic_id=data["epic_id"],
                child_tasks=data["child_tasks"],
                creator_id=data["creator_id"],
                assigned_user_id=data["assigned_user_id"],
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")

    @staticmethod
    def from_firestore(doc) -> "Story":
        data = doc.to_dict()
        return Story(
            story_id=doc.id,
            name=data["name"],
            description=data["description"],
            status=data["status"],
            epic_id=data["epic_id"],
            child_tasks=data["child_tasks"],
            creator_id=data["creator_id"],
            assigned_user_id=data["assigned_user_id"],
        )

    @staticmethod
    def to_firestore(story: "Story", db: Client) -> dict:
        story_ref = db.collection("stories").document(story.story_id)
        story_ref.set(story.to_dict())
        return story_ref


class Task:
    def __init__(
        self,
        task_id: str,
        name: str,
        description: str,
        status: str,
        creator_id: str,
        assigned_user_id: str = None,
        story_id: str = None,
    ):
        if status not in STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {STATUSES}")
        self.task_id = task_id
        self.creator_id = creator_id
        self.name = name
        self.description = description
        self.status = status
        self.story_id = story_id
        self.assigned_user_id = assigned_user_id

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "story_id": self.story_id,
            "creator_id": self.creator_id,
            "assigned_user_id": self.assigned_user_id,
        }

    @staticmethod
    def from_dict(data: dict, id: str = None):
        try:
            task = Task(
                task_id=id or uuid.uuid4().hex,
                name=data["name"],
                description=data["description"],
                status=data["status"],
                story_id=data["story_id"],
                creator_id=data["creator_id"],
                assigned_user_id=data["assigned_user_id"],
            )
            return task
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")

    @staticmethod
    def from_firestore(doc) -> "Task":
        data = doc.to_dict()
        return Task(
            task_id=doc.id,
            name=data["name"],
            description=data["description"],
            status=data["status"],
            story_id=data["story_id"],
            creator_id=data["creator_id"],
            assigned_user_id=data["assigned_user_id"],
        )

    @staticmethod
    def to_firestore(task: "Task", db: Client) -> dict:
        task_ref = db.collection("tasks").document(task.task_id)
        task_ref.set(task.to_dict())
        return task_ref
