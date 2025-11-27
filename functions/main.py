# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app, auth, firestore
from models import Epic, Story, Task
import uuid
from flask import Response

# For cost control, you can set the maximum number of containers that can be
# running at the same time. This helps mitigate the impact of unexpected
# traffic spikes by instead downgrading performance. This limit is a per-function
# limit. You can override the limit for each function using the max_instances
# parameter in the decorator, e.g. @https_fn.on_request(max_instances=5).
set_global_options(max_instances=10)

initialize_app()


@https_fn.on_call()
def upload_epic(request: https_fn.CallableRequest) -> https_fn.Response:
    epic_data = request.data
    try:
        epic = Epic.from_dict(epic_data)
    except Exception as e:
        raise https_fn.HttpsError("invalid-argument", f"Error parsing epic data: {e}")

    try:
        Epic.to_firestore(epic, firestore.client())
    except Exception as e:
        raise https_fn.HttpsError("internal", f"Error uploading epic: {e}")
    return {
        "status": "success",
        "epic_id": epic.epic_id,
    }


@https_fn.on_request()
def get_assigned_epics(req: https_fn.Request) -> https_fn.Response:
    creator_id = req.args.get("creator_id", None)
    assigned_user_id = req.args.get("assigned_user_id", None)
    status = req.args.get("status", None)
    if not assigned_user_id:
        return https_fn.Response("Missing assigned_user_id parameter", status=400)

    query_params = {
        "creator_id": creator_id,
        "assigned_user_id": assigned_user_id,
        "status": status,
    }
    # Fetch epics for the user from your database or other service
    epics = get_epics_from_db(query_params)
    return epics


@https_fn.on_call()
def upload_story(request: https_fn.CallableRequest) -> https_fn.Response:
    story_data = request.data
    try:
        story = Story.from_dict(story_data)
    except Exception as e:
        raise https_fn.HttpsError("invalid-argument", f"Error parsing story data: {e}")

    try:
        Story.to_firestore(story, firestore.client())
        return {
            "status": "success",
            "story_id": story.story_id,
        }
    except Exception as e:
        raise https_fn.HttpsError("internal", f"Error uploading story: {e}")


@https_fn.on_request()
def get_assigned_stories(req: https_fn.Request) -> https_fn.Response:
    creator_id = req.args.get("creator_id", None)
    assigned_user_id = req.args.get("assigned_user_id", None)
    epic_id = req.args.get("epic_id", None)
    status = req.args.get("status", None)
    if not assigned_user_id:
        return https_fn.Response("Missing assigned_user_id parameter", status=400)

    query_params = {
        "creator_id": creator_id,
        "assigned_user_id": assigned_user_id,
        "epic_id": epic_id,
        "status": status,
    }
    # Fetch stories for the user from your database or other service
    stories = get_stories_from_db(query_params)
    return stories


@https_fn.on_call()
def upload_task(request: https_fn.CallableRequest) -> https_fn.Response:
    task_data = request.data
    try:
        task = Task.from_dict(task_data)
    except Exception as e:
        raise https_fn.HttpsError("invalid-argument", f"Error parsing task data: {e}")

    try:
        Task.to_firestore(task, firestore.client())
    except Exception as e:
        raise https_fn.HttpsError("internal", f"Error uploading task: {e}")
    return {
        "status": "success",
        "task_id": task.task_id,
    }


@https_fn.on_request()
def get_assigned_tasks(req: https_fn.Request) -> https_fn.Response:
    creator_id = req.args.get("creator_id", None)
    assigned_user_id = req.args.get("assigned_user_id", None)
    epic_id = req.args.get("epic_id", None)
    story_id = req.args.get("story_id", None)
    status = req.args.get("status", None)
    if not assigned_user_id:
        return https_fn.Response("Missing assigned_user_id parameter", status=400)

    query_params = {
        "creator_id": creator_id,
        "assigned_user_id": assigned_user_id,
        "epic_id": epic_id,
        "story_id": story_id,
        "status": status,
    }
    # Fetch tasks for the user from your database or other service
    tasks = get_tasks_from_db(query_params)
    return tasks


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

    return [doc.to_dict() for doc in tasks_ref.stream()]


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

    return [doc.to_dict() for doc in stories_ref.stream()]


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

    return [doc.to_dict() for doc in epics_ref.stream()]
