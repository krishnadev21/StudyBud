from django.shortcuts import render, redirect
from django.http import HttpResponse
# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm

def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, "User does not exist.")

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:       
            messages.error(request, "Email or Password does not exist.")        
    return render(request, 'FirstApp/login_register.html', context={'page' : 'login'})

def registerPage(request):
    form = MyUserCreationForm()
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        try:
            if form.is_valid():
                user = form.save(commit=False)
                user.username = user.username.lower()
                user.save()
                login(request, user)
                return redirect('home')
        except Exception as e:
            messages.error(request, f'{e}')
    return render(request, 'FirstApp/login_register.html', context={'form':form})

def logoutUser(request):
    logout(request)
    return redirect('home')
    

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q) |
        Q(host__username__icontains=q)
    )
    rooms_count = rooms.count()
    topics = Topic.objects.all()[0:5]
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    return render(request, 'FirstApp/home.html', context={
        'rooms' : rooms,
        'topics' : topics, 
        'rooms_count' : rooms_count,
        'room_messages' : room_messages
    })

def userProfile(request, pk):
    user = User.objects.get(id=pk)
    room_messages = user.message_set.all()
    rooms = user.room_set.all()
    topics = Topic.objects.all()

    return render(request, 'FirstApp/profile.html', context={
        'user' : user,
        'room_messages' : room_messages,
        'rooms' : rooms,
        'topics' : topics
    })

def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all() #.order_by('-created')
    participants = room.participants.all()
    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)
    
    return render(request, 'FirstApp/room.html', context={
        'room' : room,
        'room_messages' : room_messages,
        'participants' : participants
    })

@login_required(login_url='login')
def createRoom(request):
    form = RoomForm
    topics = Topic.objects.all()
    if request.method == "POST":
            topic_name = request.POST.get('topic')
            topic, created = Topic.objects.get_or_create(name=topic_name)
            Room.objects.create(
                host=request.user,
                topic=topic,
                name=request.POST.get('name'),
                description=request.POST.get('description')
            )
        # form = RoomForm(request.POST)
        # if form.is_valid():
        #     room = form.save(commit=False)
        #     room.host = request.user
        #     # rooms.participants.add(request.user)
        #     room.save()
            return redirect('home')
        
    return render(request, 'FirstApp/room_form.html', context = {
        'form' : form,
        'topics' : topics,
        'room_method' : 'Create'
    })

@login_required(login_url='login')
def updateRoom(request, pk):
    topics = Topic.objects.all()
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    # Only the creater of the room can edit not the user
    if request.user != room.host: 
        return HttpResponse(f"<h1>{request.user} you are not allowed here!!!</h1>")
        
    if request.method == "POST":
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.topic = topic
        room.name = request.POST.get('name')
        room.description = request.POST.get('description')
        # form = RoomForm(request.POST, instance=room)
        # if form.is_valid():
        #     form.save()
        room.save()
        return redirect('home')
        
    return render(request, 'FirstApp/room_form.html', context={
        'form' : form,
        'topics' : topics,
        'room' : room,
        'room_method' : 'Update'
    })

def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    # Only the creater of the room can delete not the user
    if request.user != room.host: 
        return HttpResponse(f"<h1>{request.user} you are not allowed here!!!</h1>")
    
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    
    return render(request, 'FirstApp/delete.html', context={'obj' : room})

def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    # Only the creater of the room can delete not the user
    if request.user != message.user: 
        return HttpResponse(f"<h1>{request.user} you are not allowed here!!!</h1>")

    if request.method == 'POST':
        message.delete()
        return redirect('home')
    
    return render(request, 'FirstApp/delete.html', context={'obj' : message})

@login_required(login_url='login')
def updateUser(request):
    form = UserForm(instance=request.user)
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=request.user.id)
    return render(request, 'FirstApp/update-user.html', context={'form' : form})

def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'FirstApp/topics.html', context={'topics' : topics})

def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'FirstApp/activity.html', context={'room_messages':room_messages})

