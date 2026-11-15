from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator

# Create the FastAPI application.
app = FastAPI()

# Allow the portfolio frontend when it is served from a local development server.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


class ProjectInput(BaseModel):
    title: str
    description: str
    technology: str
    github_link: str


class Project(ProjectInput):
    id: int


class ProjectResponse(BaseModel):
    message: str
    project: Project


class ContactMessageInput(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

    @field_validator("name", "subject", "message")
    @classmethod
    def text_must_not_be_empty(cls, value: str) -> str:
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("This field must not be empty.")
        return cleaned_value


class ContactMessage(ContactMessageInput):
    id: int


class ContactMessageResponse(BaseModel):
    message: str
    id: int


# This list is temporary storage and is cleared whenever the app restarts.
projects: List[Project] = []
next_project_id = 1

# Contact messages are temporary and are cleared whenever the app restarts.
contact_messages: List[ContactMessage] = []
next_contact_message_id = 1


# Welcome visitors to the portfolio API.
@app.get("/")
def read_root():
    return {
        "message": "Welcome to my Portfolio API",
        "status": "success",
    }


# Share basic information about the portfolio owner.
@app.get("/about")
def read_about():
    return {
        "name": "Priyanshu Mohanty",
        "role": "Aspiring Software Developer",
    }


@app.post(
    "/contact",
    response_model=ContactMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_contact_message(contact_input: ContactMessageInput):
    global next_contact_message_id

    contact_message = ContactMessage(
        id=next_contact_message_id,
        **contact_input.model_dump(),
    )
    contact_messages.append(contact_message)
    next_contact_message_id += 1

    return {
        "message": "Contact message received successfully",
        "id": contact_message.id,
    }


# Return every project currently stored in memory.
@app.get("/projects", response_model=List[Project])
def get_projects():
    return projects


@app.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(project_input: ProjectInput):
    global next_project_id

    project = Project(id=next_project_id, **project_input.dict())
    projects.append(project)
    next_project_id += 1

    return {"message": "Project created successfully", "project": project}


@app.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project_input: ProjectInput):
    for index, project in enumerate(projects):
        if project.id == project_id:
            updated_project = Project(id=project_id, **project_input.dict())
            projects[index] = updated_project
            return {
                "message": "Project updated successfully",
                "project": updated_project,
            }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found",
    )


# Remove the project with the given ID.
@app.delete("/projects/{project_id}")
def delete_project(project_id: int):
    for index, project in enumerate(projects):
        if project.id == project_id:
            projects.pop(index)
            return {"message": "Project deleted successfully"}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found",
    )
