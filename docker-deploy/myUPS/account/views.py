from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, logout, login
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import *


def home(request):
    return render(request, 'home.html')


@csrf_exempt
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # User is saved
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                user_login(request)
                return redirect('user_login')  # Ensure 'login' URL is defined
            else:
                print("Authentication failed.")
        else:
            print(form.errors)  # Print form errors
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})



def user_login(request):
    if request.method == 'POST':
        # Create a form instance and populate it with data from the request
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            # Process the data in form.cleaned_data
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to a success page.
                return redirect('home')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'user_login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')



@csrf_exempt  # Consider whether you really need to exempt CSRF protection
def get_status(request):
    if request.method == 'GET':
        return render(request, 'home.html')

    elif request.method == 'POST':
        package_id = request.POST.get('package_id')

        if not package_id:
            messages.error(request, "Please enter a package ID.")
            return redirect('home')

        try:
            package = Package.objects.get(packageid=package_id)
            return render(request, 'get_status.html', {'package': package })
        except Package.DoesNotExist:
            messages.error(request, 'Package does not exist.')
            return redirect('home')
        


# @login_required 
@csrf_exempt
def user_home(request):
    return render(request, 'user_home.html')


# @login_required
def show_packages(request):
    # Retrieve all packages for the logged-in user
    packages = Package.objects.filter(user_id=request.user.id)
    
    # Pass the list of packages to the template
    return render(request, 'show_packages.html', {'packages': packages})

# @login_required
def product_details(request, package_id):
    try:
        products = Product.objects.filter(packageid=package_id)
        package = Package.objects.get(packageid=package_id)
        return render(request, 'product_details.html', {'products': products, 'user_id': package.user_id_id})
    except Package.DoesNotExist:
        messages.error(request, 'Product does not exist or you do not have permission to check it.')
        return redirect('show_packages')

# @login_required
@csrf_exempt
def modify_dest(request, package_id):
    try:
        if not request.user.id:
            # messages.error(request, 'Package does not exist or you do not have permission to modify it.')
            return redirect('user_login')
        package = Package.objects.get(packageid=package_id, user_id=request.user)

        # Check if the package status is not "delivered"
        if package.status not in ['delivered', 'out for delivery']:
            if request.method == 'POST':
                # Get new destination coordinates from the form
                new_dest_x = request.POST.get('dest_x')
                new_dest_y = request.POST.get('dest_y')

                # Update package destination coordinates
                package.dest_x = new_dest_x
                package.dest_y = new_dest_y
                package.save()
                messages.success(request, 'Destination updated successfully.')
                return redirect('show_packages')
            else:
                return render(request, 'modify_dest.html', {'package': package})
        else:
            messages.error(request, 'Cannot modify destination. Order is already delivered.')
            return redirect('show_packages')
    except Package.DoesNotExist:
        messages.error(request, 'Package does not exist or you do not have permission to modify it.')
        return redirect('show_packages')

@csrf_exempt    
def delivery_map(request, package_id):
    package = Package.objects.get(packageid=package_id)
    warehouse = package.whid
    context = {
        'package': package,
        'warehouse_x': warehouse.x,
        'warehouse_y': warehouse.y,
        'dest_x': package.dest_x,
        'dest_y': package.dest_y,
    }
    return render(request, 'delivery_map.html', context)