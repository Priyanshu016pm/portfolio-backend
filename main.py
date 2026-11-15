
import os
import smtplib
import ssl

from typing import List
from email.message import EmailMessage

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator


# Load environment variables from .env locally.
# Render will provide its own environment variables.
load_dotenv()


# Create the FastAPI application.
app = FastAPI()


# Allow requests from the deployed portfolio frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://portfolio-frontend-azure-one.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- PROJECT MODELS ----------------

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


# ---------------- CONTACT MODELS ----------------

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


# ---------------- TEMPORARY STORAGE ----------------

projects: List[Project] = []
next_project_id = 1

contact_messages: List[ContactMessage] = []
next_contact_message_id = 1


# ---------------- EMAIL FUNCTION ----------------

def send_contact_email(contact: ContactMessageInput):

    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    receiver_email = os.getenv("CONTACT_RECEIVER_EMAIL")

    if not gmail_address or not gmail_password or not receiver_email:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email service is not configured."
        )

    email = EmailMessage()

    email["Subject"] = f"Portfolio Contact: {contact.subject}"
    email["From"] = gmail_address
    email["To"] = receiver_email
    email["Reply-To"] = str(contact.email)

    email.set_content(
        f"""
You have received a new message from your portfolio.

Name: {contact.name}
Email: {contact.email}
Subject: {contact.subject}

Message:
{contact.message}
"""
    )

    try:
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            context=context,
            timeout=20
        ) as server:

            server.login(gmail_address, gmail_password)
            server.send_message(email)

    except (smtplib.SMTPException, OSError):
        # Do not expose credentials or SMTP details to visitors.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to send your message. Please try again later."
        )


# ---------------- ROOT API ----------------

@app.get("/")
def read_root():
    return {
        "message": "Welcome to my Portfolio API",
        "status": "success",
    }


# ---------------- ABOUT API ----------------

@app.get("/about")
def read_about():
    return {
        "name": "Priyanshu Mohanty",
        "role": "Aspiring Software Developer",
    }


# ---------------- CONTACT API ----------------

@app.post(
    "/contact",
    response_model=ContactMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_contact_message(contact_input: ContactMessageInput):

    global next_contact_message_id

    # Send the email first.
    send_contact_email(contact_input)

    # Store the message only after successful email delivery.
    contact_message = ContactMessage(
        id=next_contact_message_id,
        **contact_input.model_dump(),
    )

    contact_messages.append(contact_message)
    next_contact_message_id += 1

    return {
        "message": "Your message has been sent successfully!",
        "id": contact_message.id,
    }


# ---------------- GET PROJECTS ----------------

@app.get("/projects", response_model=List[Project])
def get_projects():
    return projects


# ---------------- CREATE PROJECT ----------------

@app.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(project_input: ProjectInput):

    global next_project_id

    project = Project(
        id=next_project_id,
        **project_input.model_dump()
    )

    projects.append(project)
    next_project_id += 1

    return {
        "message": "Project created successfully",
        "project": project
    }


# ---------------- UPDATE PROJECT ----------------

@app.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project_input: ProjectInput):

    for index, project in enumerate(projects):

        if project.id == project_id:

            updated_project = Project(
                id=project_id,
                **project_input.model_dump()
            )

            projects[index] = updated_project

            return {
                "message": "Project updated successfully",
                "project": updated_project
            }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found",
    )


# ---------------- DELETE PROJECT ----------------

@app.delete("/projects/{project_id}")
def delete_project(project_id: int):

    for index, project in enumerate(projects):

        if project.id == project_id:

            projects.pop(index)

            return {
                "message": "Project deleted successfully"
            }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found",
    )
