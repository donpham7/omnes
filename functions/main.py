# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app, auth, firestore
from models import Epic, Story, Task
import uuid
from flask import Response, json

# For cost control, you can set the maximum number of containers that can be
# running at the same time. This helps mitigate the impact of unexpected
# traffic spikes by instead downgrading performance. This limit is a per-function
# limit. You can override the limit for each function using the max_instances
# parameter in the decorator, e.g. @https_fn.on_request(max_instances=5).
set_global_options(max_instances=10)

initialize_app()

# ========== ITEMS ==========


# Epics
@https_fn.on_call()
def upload_epic(request: https_fn.CallableRequest) -> https_fn.Response:
    epic_data = request.data
    try:
        epic = Epic.from_dict(epic_data)
    except Exception as e:
        raise https_fn.HttpsError("invalid-argument", f"Error parsing epic data: {e}")

    try:
        epic_ref = Epic.to_firestore(epic, firestore.client())
    except Exception as e:
        raise https_fn.HttpsError("internal", f"Error uploading epic: {e}")
    return Epic.from_firestore(epic_ref.get()).to_dict()


@https_fn.on_request()
def get_epics(req: https_fn.Request) -> https_fn.Response:
    creator_id = req.args.get("creator_id", None)
    assigned_user_id = req.args.get("assigned_user_id", None)
    status = req.args.get("status", None)

    query_params = {
        "creator_id": creator_id,
        "assigned_user_id": assigned_user_id,
        "status": status,
    }
    # Fetch epics for the user from your database or other service
    epics = get_epics_from_db(query_params)
    return [epics[i].to_dict() for i in range(len(epics))]


@https_fn.on_request()
def update_epic(req: https_fn.Request) -> https_fn.Response:
    if req.method != "PATCH":
        raise https_fn.HttpsError("invalid-argument", "Invalid request method")

    id = req.args.get("id", None)
    if not id:
        raise https_fn.HttpsError("invalid-argument", "id is required")

    update_data = json.loads(req.data)["data"]
    if not update_data:
        raise https_fn.HttpsError("invalid-argument", "No data provided for update")
    try:
        return patch_epic_in_db_with_fields(id, update_data).to_dict()
    except Exception as e:
        raise https_fn.HttpsError("internal", f"Error updating epic: {e}")


@https_fn.on_request()
def get_epic_from_task(req: https_fn.Request) -> https_fn.Response:
    id = req.args.get("id", None)
    if not id:
        raise https_fn.HttpsError("invalid-argument", "id is required")

    query_params = {
        "id": id,
    }

    # Fetch Story for the task
    task = get_tasks_from_db(query_params)

    query_params = {
        "story_id": task[0].story_id,
    }
    story = get_stories_from_db(query_params)

    query_params = {
        "id": story[0].epic_id,
    }
    epic = get_epics_from_db(query_params)[0]
    return epic.to_dict()


# Stories
@https_fn.on_call()
def upload_story(request: https_fn.CallableRequest) -> https_fn.Response:
    story_data = request.data
    try:
        story = Story.from_dict(story_data)
    except Exception as e:
        raise https_fn.HttpsError("invalid-argument", f"Error parsing story data: {e}")

    try:
        story_ref = Story.to_firestore(story, firestore.client())
    except Exception as e:
        raise https_fn.HttpsError("internal", f"Error uploading story: {e}")

    if story.epic_id != "":
        try:
            # Append the new story ID to the epic's child_user_stories array
            # Get epic child_user_stories and append
            query_params = {
                "id": story.epic_id,
            }
            epic = get_epics_from_db(query_params)[0]
            if not epic:
                raise https_fn.HttpsError("not-found", "Epic not found")

            patch_epic_in_db_with_fields(
                epic.id,
                {"child_user_stories": epic.child_user_stories + [story.id]},
            )

        except Exception as e:
            story_ref.delete()
            raise https_fn.HttpsError(
                "internal", f"Error updating epic with new story: {e}"
            )
    return story.to_dict()


@https_fn.on_request()
def get_stories(req: https_fn.Request) -> https_fn.Response:
    creator_id = req.args.get("creator_id", None)
    assigned_user_id = req.args.get("assigned_user_id", None)
    epic_id = req.args.get("epic_id", None)
    status = req.args.get("status", None)

    query_params = {
        "creator_id": creator_id,
        "assigned_user_id": assigned_user_id,
        "epic_id": epic_id,
        "status": status,
    }
    # Fetch stories for the user from your database or other service
    stories = get_stories_from_db(query_params)
    return [story.to_dict() for story in stories]


@https_fn.on_request()
def update_story(req: https_fn.Request) -> https_fn.Response:
    if req.method != "PATCH":
        raise https_fn.HttpsError("invalid-argument", "Invalid request method")

    id = req.args.get("id", None)
    if not id:
        raise https_fn.HttpsError("invalid-argument", "id is required")

    update_data = json.loads(req.data)["data"]
    if not update_data:
        raise https_fn.HttpsError("invalid-argument", "No data provided for update")
    try:
        return patch_story_in_db_with_fields(id, update_data).to_dict()
    except Exception as e:
        raise https_fn.HttpsError("internal", f"Error updating story: {e}")


# Tasks
@https_fn.on_call()
def upload_task(request: https_fn.CallableRequest) -> https_fn.Response:
    task_data = request.data
    try:
        task = Task.from_dict(task_data)
    except Exception as e:
        raise https_fn.HttpsError("invalid-argument", f"Error parsing task data: {e}")

    try:
        task_ref = Task.to_firestore(task, firestore.client())
    except Exception as e:
        raise https_fn.HttpsError("internal", f"Error uploading task: {e}")

    # Update the story to include this task in its child_tasks
    if task.story_id != "":
        try:
            story = get_stories_from_db({"id": task.story_id})[0]
            if not story:
                raise https_fn.HttpsError("not-found", "Story not found")

            story = patch_story_in_db_with_fields(
                id=story.id,
                update_data={"child_tasks": story.child_tasks + [task.id]},
            )
        except Exception as e:
            task_ref.delete()
            raise https_fn.HttpsError(
                "internal", f"Error updating story with new task: {e}"
            )
    return task.to_dict()


@https_fn.on_request()
def get_tasks(req: https_fn.Request) -> https_fn.Response:
    creator_id = req.args.get("creator_id", None)
    assigned_user_id = req.args.get("assigned_user_id", None)
    epic_id = req.args.get("epic_id", None)
    story_id = req.args.get("story_id", None)
    status = req.args.get("status", None)

    query_params = {
        "creator_id": creator_id,
        "assigned_user_id": assigned_user_id,
        "epic_id": epic_id,
        "story_id": story_id,
        "status": status,
    }
    # Fetch tasks for the user from your database or other service
    tasks = get_tasks_from_db(query_params)
    return [task.to_dict() for task in tasks]


@https_fn.on_request()
def get_tasks_from_epic(req: https_fn.Request) -> https_fn.Response:
    id = req.args.get("id", None)
    if not id:
        raise https_fn.HttpsError("invalid-argument", "id is required")
    status = req.args.get("status", None)

    query_params = {
        "epic_id": id,
        "status": status,
    }
    # Fetch stories for the epic
    print("Fetching stories with query params:", query_params)
    stories_from_epic = get_stories_from_db(query_params)

    # Fetch tasks for each story
    tasks = []
    for story in stories_from_epic:
        story_id = story.id
        if story_id:
            story_query_params = {
                "story_id": story_id,
                "status": status,
            }
            story_tasks = get_tasks_from_db(story_query_params)
            tasks.extend(story_tasks)
    return [task.to_dict() for task in tasks]


@https_fn.on_request()
def update_task(req: https_fn.Request) -> https_fn.Response:
    if req.method != "PATCH":
        raise https_fn.HttpsError("invalid-argument", "Invalid request method")

    id = req.args.get("id", None)
    if not id:
        raise https_fn.HttpsError("invalid-argument", "id is required")

    update_data = json.loads(req.data)["data"]
    if not update_data:
        raise https_fn.HttpsError("invalid-argument", "No data provided for update")
    try:
        return patch_task_in_db_with_fields(id, update_data).to_dict()
    except Exception as e:
        raise https_fn.HttpsError("internal", f"Error updating task: {e}")


# ========= USER MANAGEMENT ==========
@https_fn.on_request()
def get_uid(req: https_fn.Request):
    """A function that gets the UID of a user based on their email"""
    email = req.args.get("email")
    if not email:
        return https_fn.Response("Missing email", status=400)

    uid = fetch_uid_by_email(email)
    if not uid:
        return https_fn.Response("User not found", status=404)

    return {"uid": uid}


def fetch_uid_by_email(email: str) -> str:
    try:
        user = auth.get_user_by_email(email)
        return user.uid
    except auth.UserNotFoundError:
        return None


# Helpers
def get_tasks_from_db(query_params: dict) -> list:
    # Fetch tasks from Firestore based on the query parameters
    db = firestore.client()
    tasks_ref = db.collection("tasks")

    if query_params.get("creator_id"):
        tasks_ref = tasks_ref.where("creator_id", "==", query_params["creator_id"])
    if query_params.get("assigned_user_id"):
        tasks_ref = tasks_ref.where(
            "assigned_user_id", "==", query_params["assigned_user_id"]
        )
    if query_params.get("epic_id"):
        tasks_ref = tasks_ref.where("epic_id", "==", query_params["epic_id"])
    if query_params.get("story_id"):
        tasks_ref = tasks_ref.where("story_id", "==", query_params["story_id"])
    if query_params.get("status"):
        tasks_ref = tasks_ref.where("status", "==", query_params["status"])
    if query_params.get("id"):
        tasks_ref = tasks_ref.where("id", "==", query_params["id"])

    return [Task.from_firestore(doc) for doc in tasks_ref.stream()]


def patch_task_in_db_with_fields(id: str, update_data: dict) -> None:
    db = firestore.client()
    task_ref = db.collection("tasks").document(id)
    # Only update the fields provided in update_data
    task_ref.update(update_data)
    task = Task.from_firestore(task_ref.get())
    return task


def get_stories_from_db(query_params: dict) -> list:
    # Fetch stories from Firestore based on the query parameters
    db = firestore.client()
    stories_ref = db.collection("stories")

    if query_params.get("creator_id"):
        stories_ref = stories_ref.where("creator_id", "==", query_params["creator_id"])
    if query_params.get("assigned_user_id"):
        stories_ref = stories_ref.where(
            "assigned_user_id", "==", query_params["assigned_user_id"]
        )
    if query_params.get("epic_id"):
        stories_ref = stories_ref.where("epic_id", "==", query_params["epic_id"])
    if query_params.get("status"):
        stories_ref = stories_ref.where("status", "==", query_params["status"])
    if query_params.get("story_id"):
        stories_ref = stories_ref.where("story_id", "==", query_params["story_id"])

    return [Story.from_firestore(doc) for doc in stories_ref.stream()]


def patch_story_in_db_with_fields(id: str, update_data: dict) -> None:
    db = firestore.client()
    story_ref = db.collection("stories").document(id)
    # Only update the fields provided in update_data
    story_ref.update(update_data)
    story = Story.from_firestore(story_ref.get())
    return story


def get_epics_from_db(query_params: dict) -> list:
    # Fetch epics from Firestore based on the query parameters
    db = firestore.client()
    epics_ref = db.collection("epics")

    if query_params.get("creator_id"):
        epics_ref = epics_ref.where("creator_id", "==", query_params["creator_id"])
    if query_params.get("assigned_user_id"):
        epics_ref = epics_ref.where(
            "assigned_user_id", "==", query_params["assigned_user_id"]
        )
    if query_params.get("status"):
        epics_ref = epics_ref.where("status", "==", query_params["status"])
    if query_params.get("id"):
        epics_ref = epics_ref.where("id", "==", query_params["id"])

    return [Epic.from_firestore(doc) for doc in epics_ref.stream()]


def patch_epic_in_db_with_fields(id: str, update_data: dict) -> Epic:
    db = firestore.client()
    epic_ref = db.collection("epics").document(id)
    # Only update the fields provided in update_data
    epic_ref.update(update_data)
    epic = Epic.from_firestore(epic_ref.get())
    return epic


# ========== DAILY SCHEDULE ==========
@https_fn.on_request()
def get_schedule(req: https_fn.Request) -> https_fn.Response:
    """A function that gets a user's daily schedule"""
    user_id = req.args.get("user_id")
    if not user_id:
        return https_fn.Response("Missing user_id", status=400)

    # Fetch the user's schedule from the database
    schedule = get_user_schedule(user_id)
    return https_fn.Response(schedule)


@https_fn.on_request()
def update_schedule(req: https_fn.Request) -> https_fn.Response:
    """A function that updates a user's daily schedule"""
    if req.method != "POST":
        return https_fn.Response("Invalid request method", status=400)

    user_id = req.args.get("user_id")
    if not user_id:
        return https_fn.Response("Missing user_id", status=400)

    schedule_data = json.loads(req.data).get("schedule")
    if not schedule_data:
        return https_fn.Response("Missing schedule data", status=400)

    try:
        update_user_schedule(user_id, schedule_data)
        return https_fn.Response("Schedule updated successfully", status=200)
    except Exception as e:
        return https_fn.Response(f"Error updating schedule: {e}", status=500)


# ========= HELPERS FOR SCHEDULE ==========
def get_user_schedule(user_id: str) -> dict:
    # Placeholder function to fetch user schedule from the database
    # Replace with actual database fetching logic
    return {"user_id": user_id, "schedule": "Sample Schedule"}


def update_user_schedule(user_id: str, schedule_data: dict) -> None:
    # Placeholder function to update user schedule in the database
    # Replace with actual database updating logic
    pass
