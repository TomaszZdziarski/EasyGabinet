from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Message
from patients.models import PatientProfile
from dentists.models import dentistProfile
from django.db.models import Max



@login_required
def inbox_dentist(request):
    dentist = get_object_or_404(dentistProfile, user=request.user)

    # Get latest message per patient

    patient_ids = Message.objects.filter(dentist=dentist) \
        .values('patient') \
        .annotate(latest=Max('sent_at')) \
        .order_by('-latest')

    # Build a list of latest messages per patient
    inbox = []
    for item in patient_ids:
        latest_message = Message.objects.filter(
            dentist=dentist,
            patient_id=item['patient']
        ).order_by('-sent_at').first()

        # attach unread count directly to the message object
        latest_message.unread_count = Message.objects.filter(
            dentist=dentist,
            patient_id=item['patient'],
            sender='patient',
            is_read=False
        ).count()

        inbox.append(latest_message)

    return render(request, 'messaging/inbox.html', {'inbox': inbox})

@login_required
def new_message(request):
    dentist = get_object_or_404(dentistProfile, user=request.user)
    patients = PatientProfile.objects.all()

    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        body = request.POST.get('body')
        patient = get_object_or_404(PatientProfile, id=patient_id)

        Message.objects.create(
            patient=patient,
            dentist=dentist,
            sender='dentist',
            body=body,
            is_read=False
        )
        return redirect('inbox')

    return render(request, 'messaging/new_message.html', {'patients': patients})

@login_required
def conversation(request, patient_id):


    dentist = get_object_or_404(dentistProfile, user=request.user)
    patient = get_object_or_404(PatientProfile, id=patient_id)

    thread = Message.objects.filter(
        dentist=dentist,
        patient=patient
    ).order_by('sent_at')

    # mark all patient messages as read
    thread.filter(sender='patient', is_read=False).update(is_read=True)

    if request.method == 'POST':
        body = request.POST.get('body')
        Message.objects.create(
            patient=patient,
            dentist=dentist,
            sender='dentist',
            body=body,
            is_read=False
        )
        return redirect('conversation', patient_id=patient_id)

    return render(request, 'messaging/conversation.html', {
        'thread': thread,
        'patient': patient
    })

@login_required
def delete_message(request, pk):
    message = get_object_or_404(Message, id=pk)
    message.delete()
    return redirect('inbox')

@login_required
def patient_inbox(request):
    patient = get_object_or_404(PatientProfile, user=request.user)
    dentist = patient.linked_dentist

    if not dentist:
        return render(request, 'messaging/no_dentist.html')

    from django.db.models import Max
    thread = Message.objects.filter(
        patient=patient,
        dentist=dentist
    ).order_by('sent_at')

    # mark dentist messages as read
    thread.filter(sender='dentist', is_read=False).update(is_read=True)

    if request.method == 'POST':
        body = request.POST.get('body')
        Message.objects.create(
            patient=patient,
            dentist=dentist,
            sender='patient',
            body=body,
            is_read=False
        )
        return redirect('patient-inbox')

    unread_count = thread.filter(sender='dentist', is_read=False).count()

    return render(request, 'messaging/patient_inbox.html', {
        'thread': thread,
        'dentist': dentist,
        'patient': patient,
        'unread_count': unread_count,
    })