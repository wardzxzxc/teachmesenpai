from django.contrib.auth.decorators import login_required
from django.conf import settings
try:
    from django.contrib.auth import get_user_model
    user_model = get_user_model()
except ImportError:
    from django.contrib.auth.models import User
    user_model = User

from django.shortcuts import render, get_object_or_404, redirect
from friendship.exceptions import AlreadyExistsError
from friendship.models import Friend, Follow, FriendshipRequest, FriendshipManager
from accountsregistration.models import AccountsProfile
get_friendship_context_object_name = lambda: getattr(settings, 'FRIENDSHIP_CONTEXT_OBJECT_NAME', 'user')
get_friendship_context_object_list_name = lambda: gfriendship_request_sent_listetattr(settings, 'FRIENDSHIP_CONTEXT_OBJECT_LIST_NAME', 'users')


@login_required
def view_friends(request, username, template_name='friendship/friend/user_list.html'):
    """ View the friends of a user """
    # user = request.user
    user = get_object_or_404(user_model, username=request.user)
    friends = Friend.objects.friends(user)
    return render(request, template_name, {
        get_friendship_context_object_name(): user,
        'friendship_context_object_name': get_friendship_context_object_name()
    })


@login_required
def view_tutees(request, template_name = 'friendship/friend/tutee_list.html'):
    user = request.user
    ctx = {'friends' : Friend.objects.all().filter(to_user = user)}
    return render(request, template_name, ctx)

@login_required #request from tutee to tutor
def friendship_add_tutor(request, to_username, template_name='friendship/friend/add_tutor.html'):
    """ Create a FriendshipRequest """
    ctx = {'to_username': to_username}

    if request.method == 'POST':
        to_user = user_model.objects.get(username=to_username)
        from_user = request.user
        try:
            Friend.objects.add_friend(from_user, to_user)
        except AlreadyExistsError as e:
            ctx['errors'] = ["%s" % e]
        else:
            return redirect('tutor_request_sent_list')

    return render(request, template_name, ctx)

@login_required #request from tutor to tutee
def friendship_add_tutee(request, to_username, template_name='friendship/friend/add_tutee.html'):
    """ Create a FriendshipRequest """
    ctx = {'to_username': to_username}

    if request.method == 'POST':
        to_user = user_model.objects.get(username=to_username)
        from_user = request.user
        try:
            Friend.objects.add_friend(from_user, to_user)
        except AlreadyExistsError as e:
            ctx['errors'] = ["%s" % e]
        else:
            return redirect('tutor_request_sent_list')

    return render(request, template_name, ctx)


@login_required #accept by tutor
def friendship_accept(request, friendship_request_id):
    """ Accept a friendship request """
    if request.method == 'POST':
        f_request = get_object_or_404(
            request.user.friendship_requests_received,
            id=friendship_request_id)
        tutee = AccountsProfile.objects.get(user = f_request.from_user)
        tutor = AccountsProfile.objects.get(user = f_request.to_user)
        tutee.points -= tutor.tuition_cost
        tutor.points += tutor.tuition_cost
        tutee.save()
        tutor.save()
        f_request.accept()
        return redirect('friendship_view_friends', username=request.user.username)

    return redirect('friendship_requests_detail', friendship_request_id=friendship_request_id)

@login_required #accept by tutee
def friendship_accept_tutee(request, friendship_request_id):
    """ Accept a friendship request """
    if request.method == 'POST':
        f_request = get_object_or_404(
            request.user.friendship_requests_received,
            id=friendship_request_id)
        tutor = AccountsProfile.objects.get(user = f_request.from_user)
        tutee = AccountsProfile.objects.get(user = f_request.to_user)
        tutee_request = TuteeRequest.objects.get(user = f_request.to_user)
        tutee.points -= tutee_request.expected_cost
        tutor.points += tutee_request.expected_costs
        tutee.save()
        tutor.save()
        f_request.accept()
        return redirect('friendship_view_friends', username=request.user.username)

    return redirect('friendship_requests_detail', friendship_request_id=friendship_request_id)


@login_required
def friendship_reject(request, friendship_request_id):
    """ Reject a friendship request """
    if request.method == 'POST':
        f_request = get_object_or_404(
            request.user.friendship_requests_received,
            id=friendship_request_id)
        f_request.reject()
        return redirect('friendship_request_received_list')

    return redirect('friendship_requests_detail', friendship_request_id=friendship_request_id)


@login_required
def friendship_cancel(request, friendship_request_id):
    """ Cancel a previously created friendship_request_id """
    if request.method == 'POST':
        f_request = get_object_or_404(
            request.user.friendship_requests_sent,
            id=friendship_request_id)
        f_request.cancel()
        return redirect('friendship_request_received_list')

    return redirect('friendship_requests_detail', friendship_request_id=friendship_request_id)


# @login_required
# def friendship_request_list(request, template_name='friendship/friend/requests_list.html'):
#     """ View unread and read friendship requests """
#     # friendship_requests = Friend.objects.requests(request.user)
#     friendship_requests = FriendshipRequest.objects.filter(rejected__isnull=True)

#     return render(request, template_name, {'requests': friendship_requests})
@login_required
def friendship_received_list(request, template_name='friendship/friend/tutee_requests_received_list.html'):
    """ View all received tutee requests """
    # friendship_requests = Friend.objects.requests(request.user)
    all_friendship_requests = FriendshipRequest.objects.filter(rejected__isnull=True)
    received_requests = []
    for friendship_request in all_friendship_requests:
        if friendship_request.to_user == request.user:
            received_requests.append(friendship_request)

    return render(request, template_name, {'requests': received_requests})

@login_required
def friendship_sent_list(request, template_name='friendship/friend/tutor_requests_sent_list.html'):
    """View all sent tutor requests"""
    sent_requests = Friend.objects.sent_requests(request.user)

    return render(request, template_name, {'requests': sent_requests})


@login_required
def friendship_request_list_rejected(request, template_name='friendship/friend/requests_list.html'):
    """ View rejected friendship requests """
    # friendship_requests = Friend.objects.rejected_requests(request.user)
    friendship_requests = FriendshipRequest.objects.filter(rejected__isnull=True)

    return render(request, template_name, {'requests': friendship_requests})


@login_required
def friendship_requests_detail(request, friendship_request_id, template_name='friendship/friend/request.html'):
    """ View a particular friendship request """
    f_request = get_object_or_404(FriendshipRequest, id=friendship_request_id)

    return render(request, template_name, {'friendship_request': f_request})


def followers(request, username, template_name='friendship/follow/followers_list.html'):
    """ List this user's followers """
    user = get_object_or_404(user_model, username=username)
    followers = Follow.objects.followers(user)

    return render(request, template_name, {
        get_friendship_context_object_name(): user,
        'friendship_context_object_name': get_friendship_context_object_name()
    })


def following(request, username, template_name='friendship/follow/following_list.html'):
    """ List who this user follows """
    user = get_object_or_404(user_model, username=username)
    following = Follow.objects.following(user)

    return render(request, template_name, {
        get_friendship_context_object_name(): user,
        'friendship_context_object_name': get_friendship_context_object_name()
    })


@login_required
def follower_add(request, followee_username, template_name='friendship/follow/add.html'):
    """ Create a following relationship """
    ctx = {'followee_username': followee_username}

    if request.method == 'POST':
        followee = user_model.objects.get(username=followee_username)
        follower = request.user
        try:
            Follow.objects.add_follower(follower, followee)
        except AlreadyExistsError as e:
            ctx['errors'] = ["%s" % e]
        else:
            return redirect('friendship_following', username=follower.username)

    return render(request, template_name, ctx)


@login_required
def follower_remove(request, followee_username, template_name='friendship/follow/remove.html'):
    """ Remove a following relationship """
    if request.method == 'POST':
        followee = user_model.objects.get(username=followee_username)
        follower = request.user
        Follow.objects.remove_follower(follower, followee)
        return redirect('friendship_following', username=follower.username)

    return render(request, template_name, {'followee_username': followee_username})


def all_users(request, template_name="friendship/user_actions.html"):
    users = user_model.objects.all()

    return render(request, template_name, {get_friendship_context_object_list_name(): users})
