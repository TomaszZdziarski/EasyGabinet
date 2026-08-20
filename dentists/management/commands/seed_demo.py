"""
Management command that creates a complete set of demonstration data.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --reset    # removes previous demo data first

Location: dentists/management/commands/seed_demo.py
Both management/ and commands/ must contain an empty __init__.py file,
otherwise Django will not find the command.

Note: this command never touches accounts other than the two demo ones.
Without --reset everything goes through get_or_create / update_or_create,
so running it twice does not duplicate anything.
"""

from datetime import date, time, timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from PIL import Image

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from dentists.models import dentistProfile, DentistSchedule, Skill, Project, Tag
from patients.models import PatientProfile, Document
from appointments.models import Appointment, AppointmentPurpose

# NOTE: replace 'messages_app' with the app that actually holds the Message model
from messaging.models import Message

User = get_user_model()


# --- demo data kept in one place so it is easy to change ------------------

DENTIST_EMAIL = "demo.dentist@easygabinet.pl"
PATIENT_EMAIL = "demo.patient@easygabinet.pl"
DEMO_PASSWORD = "demo1234"

BRAND_BLUE = (240, 247, 255)
BRAND_NAVY = (240, 247, 255)
BRAND_SLATE = (240, 247, 255)
BRAND_GREEN = (240, 247, 255)


class Command(BaseCommand):
    help = "Creates demo accounts (dentist + patient) with appointments, messages, skills and projects."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Deletes the existing demo accounts before creating new ones.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.reset()

        dentist = self.create_dentist()
        patient = self.create_patient(dentist)

        self.create_schedule(dentist)
        purposes = self.create_purposes(dentist)
        self.create_skills(dentist)          # must run before create_projects
        self.create_projects(dentist)
        self.create_appointments(dentist, patient, purposes)
        self.create_messages(dentist, patient)
        self.create_document(patient)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(f"  dentist: {DENTIST_EMAIL} / {DEMO_PASSWORD}")
        self.stdout.write(f"  patient: {PATIENT_EMAIL} / {DEMO_PASSWORD}")

    # --- deletion ---------------------------------------------------------

    def reset(self):
        """Removes the demo accounts only. CASCADE clears their profiles,
        appointments, messages, documents, skills and projects.
        No other account is affected."""
        deleted, _ = User.objects.filter(
            email__in=[DENTIST_EMAIL, PATIENT_EMAIL]
        ).delete()
        self.stdout.write(self.style.WARNING(f"Removed {deleted} demo objects."))

    # --- helper: skill artwork -------------------------------------------

    def make_icon(self, kind, bg, size=(600, 400)):
        """Places a demo icon on a brand-coloured field.

        The source files live in static/demo/ and are transparent PNGs, so the
        alpha channel is used as the paste mask and the colour shows through.
        If the file is missing, falls back to a plain field rather than failing
        the whole seed.

        Nothing is written to disk here. The caller hands the bytes to
        FieldFile.save(), which routes them through Django's storage backend:
        the local filesystem in development, S3 in production.
        """
        image = Image.new("RGB", size, bg)

        path = Path(settings.BASE_DIR) / "static" / "demo" / f"{kind}.png"
        if path.exists():
            icon = Image.open(path).convert("RGBA")

            # scale to about 55% of the shorter side, keeping proportions
            target = int(min(size) * 0.55)
            icon = icon.resize((target, target), Image.LANCZOS)

            ox = int((size[0] - target) / 2)
            oy = int((size[1] - target) / 2)
            image.paste(icon, (ox, oy), icon)      # third argument = alpha mask

        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=88)
        return buffer.getvalue()

    def make_plain(self, color, size=(600, 400)):
        """Plain brand-coloured field, no icon. Used for project covers."""
        image = Image.new("RGB", size, color)
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=88)
        return buffer.getvalue()

    # --- accounts ---------------------------------------------------------

    def create_dentist(self):
        user, created = User.objects.get_or_create(
            email=DENTIST_EMAIL,
            defaults={
                "first_name": "Anna",
                "last_name": "Kowalska",
                "user_type": "dentist",
                "pesel": "00000000000",
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()

        # update_or_create, not get_or_create: the createProfile signal already
        # made an empty profile when the user was saved, so get_or_create would
        # find it and silently skip everything in defaults.
        profile, _ = dentistProfile.objects.update_or_create(
            user=user,
            defaults={
                "phone_number": "600100200",
                "short_intro": "Restorative dentistry and endodontics",
                "bio": (
                    "I have been practising restorative dentistry and endodontics "
                    "for over a decade, with a particular interest in saving teeth "
                    "that other clinics have written off. Most of my work is root "
                    "canal treatment under magnification, followed by the crown or "
                    "composite restoration that goes with it.\n\n"
                    "I try to explain what I am doing before I do it. Patients who "
                    "understand the plan tend to come back for the second "
                    "appointment, which matters more than it sounds.\n\n"
                    "Demo account — everything on this profile is fictional and "
                    "exists only to demonstrate the application."
                ),
                "university": "Medical University",
                "function": "dentist",
                "social_website": "https://example.com",

            },
        )


        self.stdout.write(f"dentist:  {profile.get_full_name()}")
        return profile

    def create_patient(self, dentist):
        user, created = User.objects.get_or_create(
            email=PATIENT_EMAIL,
            defaults={
                "first_name": "Peter",
                "last_name": "Novak",
                "user_type": "patient",
                "pesel": "00000000001",
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()

        profile, _ = PatientProfile.objects.update_or_create(
            user=user,
            defaults={
                "address": "1 Example Street, Warsaw",
                "phone_number": "600300400",
                "date_of_birth": date(1985, 4, 12),
            },
        )
        # linking the patient to the dentist - without this the message inbox stays empty
        profile.linked_dentists.add(dentist)

        self.stdout.write(f"patient:  {profile}")
        return profile

    # --- schedule and price list ------------------------------------------

    def create_schedule(self, dentist):
        """Working hours Mon-Wed, 9:00-17:00."""
        for day in range(3):
            DentistSchedule.objects.get_or_create(
                dentist=dentist,
                day_of_week=day,
                defaults={"start_time": time(9, 0), "end_time": time(17, 0)},
            )
        self.stdout.write("schedule: Mon-Fri 9:00-17:00")

    def create_purposes(self, dentist):
        data = [
            ("Consultation", Decimal("150.00")),
            ("Filling", Decimal("350.00")),
            ("Root canal treatment", Decimal("900.00")),
            ("Scaling and polishing", Decimal("250.00")),
        ]
        purposes = []
        for name, price in data:
            purpose, _ = AppointmentPurpose.objects.get_or_create(
                owner=dentist,
                purpose=name,
                defaults={"price_PLN": price},
            )
            purposes.append(purpose)
        self.stdout.write(f"prices:   {len(purposes)} entries")
        return purposes

    # --- skills -----------------------------------------------------------

    def create_skills(self, dentist):
        """Four skills with tags and generated cover images."""
        data = [
            ("Endodontics",
             "Root canal treatment under magnification, including retreatment of "
             "canals filled elsewhere. Rotary instrumentation and warm vertical "
             "obturation.",
             ["endodontics", "microscope"],
             BRAND_BLUE, "endodontics"),
            ("Prosthodontics",
             "Crowns, bridges and veneers. Digital impressions where the case "
             "allows, with shade matching done in daylight.",
             ["prosthetics", "crowns"],
             BRAND_NAVY, "prosthodontics"),
            ("Restorative dentistry",
             "Composite fillings, inlays and onlays. A minimally invasive "
             "approach, keeping as much healthy tissue as possible.",
             ["fillings", "composite"],
             BRAND_SLATE, "restorative"),
            ("Preventive care",
             "Scaling, air polishing and fluoride treatment. Hygiene instruction "
             "adapted to what the patient will realistically keep up.",
             ["hygiene", "prevention"],
             BRAND_GREEN, "preventive"),
        ]

        new = 0
        for name, description, tag_names, color, icon in data:
            skill, created = Skill.objects.get_or_create(
                owner=dentist,
                name=name,
                defaults={"description": description},
            )

            # tags are shared between skills, so match them by name
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                skill.tags.add(tag)

            # the guard matters: without it every run would upload a new file
            if not skill.skill_image:
                skill.skill_image.save(
                    f"demo_skill_{name.lower().replace(' ', '_')}.jpg",
                    ContentFile(self.make_icon(icon, color)),
                    save=True,
                )

            new += int(created)

        self.stdout.write(f"skills:   {len(data)} total, {new} new")

    # --- projects ---------------------------------------------------------

    def create_projects(self, dentist):
        """Two case-study style projects, each linked to the skills involved."""
        data = [
            ("Full mouth rehabilitation",
             "A staged case combining endodontic treatment, three crowns and the "
             "replacement of old amalgam fillings. Spread over four months to fit "
             "around the patient's own schedule.",
             ["Endodontics", "Prosthodontics"],
             ["case study", "rehabilitation"],
             BRAND_BLUE,"project1"),
            ("Anterior aesthetic restoration",
             "Two central incisors rebuilt with layered composite after trauma. "
             "Shade taken in daylight, final polishing at a second appointment.",
             ["Restorative dentistry"],
             ["aesthetics", "composite"],
             BRAND_NAVY,"project2"),
        ]

        new = 0
        for name, description, skill_names, tag_names, color,icon in data:
            project, created = Project.objects.get_or_create(
                owner=dentist,
                name=name,
                defaults={"description": description},
            )

            # skills must already exist - hence create_skills runs first
            for skill_name in skill_names:
                skill = Skill.objects.filter(owner=dentist, name=skill_name).first()
                if skill:
                    project.skill_used.add(skill)

            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                project.tags.add(tag)

            if not project.project_image:
                project.project_image.save(
                    f"demo_project_{name.lower().replace(' ', '_')}.jpg",
                    ContentFile(self.make_icon(icon,color)),
                    save=True,
                )

            dentist.particip_project.add(project)
            new += int(created)

        self.stdout.write(f"projects: {len(data)} total, {new} new")

    # --- appointments -----------------------------------------------------

    def create_appointments(self, dentist, patient, purposes):
        today = timezone.localdate()
        consultation, filling, root_canal, hygiene = purposes

        # past appointments that took place
        history = [
            (today - timedelta(days=90), time(10, 0), consultation, "completed",
             "Caries", "Teeth 16 and 17 need restorative treatment."),
            (today - timedelta(days=60), time(11, 30), filling, "completed",
             "Caries, tooth 16", "Composite filling placed."),
            (today - timedelta(days=30), time(9, 0), hygiene, "completed",
             "Calculus build-up", "Scaling and air polishing done."),
        ]

        # one no-show - shows the did_not_occur status without blocking the account
        history.append(
            (today - timedelta(days=14), time(15, 0), consultation, "did_not_occur",
             "None", "Patient did not attend the appointment.")
        )

        for day, hour, purpose, status, diagnosis, description in history:
            Appointment.objects.get_or_create(
                dentist=dentist,
                patient=patient,
                date=day,
                start_time=hour,
                defaults={
                    "user": patient.user,
                    "name": purpose.purpose,
                    "purpose": purpose,
                    "status": status,
                    "diagnosis": diagnosis,
                    "description": description,
                    "converted_price": purpose.price_PLN,
                    "currency": "PLN",
                    "confirmation_status": Appointment.ConfirmationStatus.CONFIRMED,
                },
            )

        # an upcoming booked appointment
        Appointment.objects.get_or_create(
            dentist=dentist,
            patient=patient,
            date=today + timedelta(days=7),
            start_time=time(12, 0),
            defaults={
                "user": patient.user,
                "name": root_canal.purpose,
                "purpose": root_canal,
                "status": "booked",
                "diagnosis": "Pulpitis, tooth 26",
                "description": "Root canal treatment planned, first visit.",
                "converted_price": root_canal.price_PLN,
                "currency": "PLN",
                "confirmation_status": Appointment.ConfirmationStatus.CONFIRMED,
            },
        )

        # free slots - so the calendar has something to show visitors
        free = 0
        for offset in range(1, 15):
            day = today + timedelta(days=offset)
            if day.weekday() >= 5:           # skip weekends
                continue
            for hour in (time(9, 0), time(10, 30), time(14, 0), time(15, 30)):
                _, created = Appointment.objects.get_or_create(
                    dentist=dentist,
                    date=day,
                    start_time=hour,
                    patient=None,
                    defaults={
                        "name": "Available slot",
                        "purpose": consultation,
                        "status": "available",
                    },
                )
                free += int(created)

        self.stdout.write(f"visits:   {len(history) + 1} in history, {free} free slots")

    # --- messages ---------------------------------------------------------

    def create_messages(self, dentist, patient):
        if Message.objects.filter(dentist=dentist, patient=patient).exists():
            self.stdout.write("messages: already present, skipping")
            return

        thread = [
            ("patient", "Hello, can I eat straight after having a filling done?", True),
            ("dentist", "Hello. Composite hardens immediately, so there is no need "
                        "to wait before eating. Just go easy on very hard food for "
                        "the first day or so.", True),
            ("patient", "Thank you. Is there anything I should do to prepare for "
                        "the root canal treatment?", True),
            ("dentist", "Nothing special - have a light meal beforehand and set "
                        "aside about an hour. See you then.", False),
        ]

        for sender, body, is_read in thread:
            Message.objects.create(
                patient=patient,
                dentist=dentist,
                sender=sender,
                body=body,
                is_read=is_read,
            )

        self.stdout.write(f"messages: {len(thread)} in thread")

    # --- document ---------------------------------------------------------

    def create_document(self, patient):
        if patient.documents.exists():
            self.stdout.write("documents: already present, skipping")
            return

        content = (
            "DEMONSTRATION MEDICAL HISTORY\n"
            "=============================\n\n"
            "Sample document, generated automatically.\n"
            "Contains no data belonging to a real patient.\n\n"
            "Chronic conditions: none\n"
            "Current medication: none\n"
            "Allergies: none known\n"
        )
        document = Document(patient=patient)
        document.file.save(
            "medical_history_demo.txt",
            ContentFile(content.encode("utf-8")),
            save=True,
        )
        self.stdout.write("documents: 1 sample file")