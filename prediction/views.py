from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from datetime import date, datetime
import json
import os
import pickle
import shutil
from .models import Community, DailyFloodRisk, Profile, SystemLog
from .weather_fetcher import get_daily_weather
from django.conf import settings
from django.db.models import Q

# ==================== LOGGING UTILITY ====================

def log_system_action(user, action, description, ip_address=None):
    """
    Helper function to log system actions.
    """
    SystemLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=ip_address
    )

# ==================== BACKUP & RESTORE ====================

@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='dashboard')
def backup_restore_view(request):
    """
    Backup and restore page – shows real backup files from the backups directory.
    """
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    backups = []
    total_size = 0
    for filename in os.listdir(backup_dir):
        if filename.endswith('.sqlite3'):
            filepath = os.path.join(backup_dir, filename)
            stat = os.stat(filepath)
            size_mb = stat.st_size / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB"
            total_size += stat.st_size
            try:
                date_part = filename.replace('backup_', '').replace('.sqlite3', '')
                date_obj = datetime.strptime(date_part, '%Y-%m-%d_%H-%M')
                date_str = date_obj.strftime('%Y-%m-%d %H:%M')
            except:
                date_str = 'Unknown'
            backups.append({
                'filename': filename,
                'date': date_str,
                'size': size_str,
                'filepath': filepath,
            })

    backups.sort(key=lambda x: x['date'], reverse=True)

    total_backups = len(backups)
    latest_backup = backups[0]['date'] if backups else 'None'
    total_size_mb = total_size / (1024 * 1024)
    backup_size = f"{total_size_mb:.1f} MB" if total_size_mb > 0 else '0 MB'

    context = {
        'latest_backup': latest_backup,
        'backup_size': backup_size,
        'total_backups': total_backups,
        'backups': backups,
    }
    return render(request, 'backup_restore.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='dashboard')
def create_backup(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        db_path = settings.DATABASES['default']['NAME']
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        backup_filename = f'backup_{timestamp}.sqlite3'
        backup_path = os.path.join(backup_dir, backup_filename)
        shutil.copy2(db_path, backup_path)

        log_system_action(
            request.user,
            'BACKUP_CREATED',
            f"Backup created: {backup_filename}",
            request.META.get('REMOTE_ADDR')
        )

        return JsonResponse({
            'success': True,
            'message': f'Backup created: {backup_filename}',
            'filename': backup_filename
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='dashboard')
def download_backup(request, filename):
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    filepath = os.path.join(backup_dir, filename)
    if not os.path.exists(filepath) or not filename.endswith('.sqlite3'):
        raise Http404("Backup file not found.")
    response = FileResponse(open(filepath, 'rb'), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='dashboard')
def restore_backup(request, filename):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    filepath = os.path.join(backup_dir, filename)
    if not os.path.exists(filepath) or not filename.endswith('.sqlite3'):
        return JsonResponse({'error': 'Backup file not found.'}, status=404)
    db_path = settings.DATABASES['default']['NAME']
    try:
        shutil.copy2(filepath, db_path)
        return JsonResponse({'success': True, 'message': f'Database restored successfully from {filename}.'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='dashboard')
def delete_backup(request, filename):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    filepath = os.path.join(backup_dir, filename)
    if not os.path.exists(filepath) or not filename.endswith('.sqlite3'):
        return JsonResponse({'error': 'Backup file not found.'}, status=404)
    try:
        os.remove(filepath)
        return JsonResponse({'success': True, 'message': f'Backup {filename} deleted successfully.'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ==================== REPORTS ====================

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='dashboard')
def reports_view(request):
    predictions = DailyFloodRisk.objects.all()
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    risk = request.GET.get('risk')

    if date_from:
        predictions = predictions.filter(date__gte=date_from)
    if date_to:
        predictions = predictions.filter(date__lte=date_to)
    if risk:
        predictions = predictions.filter(risk_level=risk)

    total_predictions = predictions.count()
    total_alerts = predictions.filter(flood_risk=True).count()
    high_risk_communities = predictions.filter(risk_level='HIGH').values('community').distinct().count()
    today = date.today()
    active_alerts = predictions.filter(date=today, flood_risk=True).count()

    community_reports = []
    communities = Community.objects.all()
    for comm in communities:
        comm_preds = predictions.filter(community=comm)
        if comm_preds.exists():
            alerts = comm_preds.filter(flood_risk=True).count()
            latest = comm_preds.order_by('-date').first()
            risk_level = latest.risk_level if latest else 'LOW'
            community_reports.append({
                'community': comm.name,
                'predictions': comm_preds.count(),
                'alerts': alerts,
                'risk': risk_level,
            })
        else:
            community_reports.append({
                'community': comm.name,
                'predictions': 0,
                'alerts': 0,
                'risk': 'LOW',
            })

    context = {
        'total_predictions': total_predictions,
        'total_alerts': total_alerts,
        'high_risk_communities': high_risk_communities,
        'active_alerts': active_alerts,
        'reports': community_reports,
        'date_from': date_from,
        'date_to': date_to,
        'risk_filter': risk,
    }
    return render(request, 'reports.html', context)


@login_required
def api_update_profile(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    data = json.loads(request.body)
    user = request.user
    if 'fullName' in data:
        user.first_name = data['fullName']
    if 'email' in data:
        user.email = data['email']
    user.save()
    if hasattr(user, 'profile') and 'phone' in data:
        user.profile.phone = data['phone']
        user.profile.save()
    return JsonResponse({'success': True, 'message': 'Profile updated'})


# ==================== SYSTEM LOGS ====================

from django.contrib.auth.models import User

@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='dashboard')
def system_logs_view(request):
    logs_qs = SystemLog.objects.all().order_by('-created_at')
    total_logs = logs_qs.count()
    login_events = logs_qs.filter(action='LOGIN').count()

    q_filter = Q(rainfall_mm__gt=0) | Q(temperature_c__gt=0) | Q(humidity_percent__gt=0) | Q(soil_moisture__gt=0)
    valid_predictions = DailyFloodRisk.objects.filter(q_filter).distinct()
    alert_events = valid_predictions.count()

    system_errors = logs_qs.filter(action='SYSTEM_ERROR').count()
    logs_display = logs_qs[:100]
    log_list = []
    for log in logs_display:
        log_list.append({
            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M'),
            'user': log.user.username if log.user else 'System',
            'activity': f"{log.get_action_display()}: {log.description}",
            'status': 'Success' if log.action != 'SYSTEM_ERROR' else 'Error',
        })
    context = {
        'total_logs': total_logs,
        'login_events': login_events,
        'alert_events': alert_events,
        'system_errors': system_errors,
        'logs': log_list,
    }
    return render(request, 'system_logs.html', context)


# ==================== DISASTER MANAGER PROFILE ====================

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='dashboard')
def manager_profile(request):
    user = request.user
    valid_predictions = DailyFloodRisk.objects.filter(
        Q(rainfall_mm__gt=0) | Q(temperature_c__gt=0) | Q(humidity_percent__gt=0) | Q(soil_moisture__gt=0)
    ).distinct()
    communities_managed = valid_predictions.values('community').distinct().count()
    alerts_issued = valid_predictions.count()
    reports_generated = valid_predictions.count()
    emergency_responses = valid_predictions.filter(risk_level='HIGH').count()
    phone = user.profile.phone if hasattr(user, 'profile') and hasattr(user.profile, 'phone') else 'Not provided'
    context = {
        'communities_managed': communities_managed,
        'alerts_issued': alerts_issued,
        'reports_generated': reports_generated,
        'emergency_responses': emergency_responses,
        'full_name': user.get_full_name(),
        'username': user.username,
        'email': user.email,
        'phone': phone,
    }
    return render(request, 'manager_profile.html', context)


# ==================== PLACEHOLDER VIEWS ====================

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='dashboard')
def alerts_management(request):
    return render(request, 'alerts_management.html')


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='dashboard')
def communities_view(request):
    return render(request, 'communities.html')


# ==================== HISTORY (API‑Driven) ====================

@login_required
@user_passes_test(lambda u: u.is_staff, login_url='dashboard')
def history_view(request):
    return render(request, 'history.html')


# ==================== AUTH & PAGES ====================

@login_required
@user_passes_test(lambda u: u.is_staff)
def api_send_warning(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        pred_id = data.get('id')
        if not pred_id:
            return JsonResponse({'error': 'Prediction ID required'}, status=400)
        prediction = DailyFloodRisk.objects.get(id=pred_id)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Warning sent for {prediction.community.name} on {prediction.date} "
            f"by {request.user.username}"
        )
        log_system_action(
            request.user,
            'ALERT_SENT',
            f"Warning sent for {prediction.community.name} on {prediction.date}",
            request.META.get('REMOTE_ADDR')
        )
        return JsonResponse({
            'success': True,
            'message': f'Warning sent for {prediction.community.name} on {prediction.date}.'
        })
    except DailyFloodRisk.DoesNotExist:
        return JsonResponse({'error': 'Prediction not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(lambda u: u.is_staff)
def api_resolve_alert(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        pred_id = data.get('id')
        if not pred_id:
            return JsonResponse({'error': 'Prediction ID required'}, status=400)
        prediction = DailyFloodRisk.objects.get(id=pred_id)
        community_name = prediction.community.name
        pred_date = prediction.date
        prediction.delete()
        log_system_action(
            request.user,
            'ALERT_RESOLVED',
            f"Alert resolved for {community_name} on {pred_date}",
            request.META.get('REMOTE_ADDR')
        )
        return JsonResponse({
            'success': True,
            'message': f'Alert for {community_name} on {pred_date} resolved.'
        })
    except DailyFloodRisk.DoesNotExist:
        return JsonResponse({'error': 'Prediction not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def home_page(request):
    communities = Community.objects.all().order_by('name')
    total_communities = communities.count()
    total_predictions = DailyFloodRisk.objects.count()
    high_risk_today = DailyFloodRisk.objects.filter(date=date.today(), risk_level='HIGH').count()
    ai_accuracy = 95
    emergency_centres = 12
    context = {
        'communities': communities,
        'total_communities': total_communities,
        'total_predictions': total_predictions,
        'high_risk_today': high_risk_today,
        'ai_accuracy': ai_accuracy,
        'emergency_centres': emergency_centres,
        'today': date.today(),
    }
    return render(request, 'home.html', context)


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            log_system_action(
                user,
                'LOGIN',
                f"User {user.username} logged in",
                request.META.get('REMOTE_ADDR')
            )
            if user.is_superuser:
                return redirect('dashboard')
            elif user.is_staff:
                return redirect('disaster_manager_dashboard')
            else:
                return redirect('community_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        log_system_action(
            request.user,
            'LOGOUT',
            f"User {request.user.username} logged out",
            request.META.get('REMOTE_ADDR')
        )
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    if not request.user.is_superuser:
        if request.user.is_staff:
            return redirect('disaster_manager_dashboard')
        else:
            return redirect('community_dashboard')
    today_risks = DailyFloodRisk.objects.filter(date=date.today()).select_related('community')
    high_count = today_risks.filter(risk_level='HIGH').count()
    moderate_count = today_risks.filter(risk_level='MODERATE').count()
    low_count = today_risks.filter(risk_level='LOW').count()
    context = {
        'risks': today_risks,
        'today': date.today(),
        'high_count': high_count,
        'moderate_count': moderate_count,
        'low_count': low_count,
    }
    return render(request, 'dashboard.html', context)


def get_today_risk(community):
    risk = DailyFloodRisk.objects.filter(community=community, date=date.today()).first()
    return risk.risk_level if risk else None


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='dashboard')
def disaster_manager_dashboard(request):
    total_communities = Community.objects.count()
    high_risk = DailyFloodRisk.objects.filter(
        date=date.today(),
        risk_level='HIGH'
    ).values('community').distinct().count()
    active_alerts = DailyFloodRisk.objects.filter(
        date=date.today(),
        flood_risk=True
    ).count()
    predictions_today = DailyFloodRisk.objects.filter(date=date.today()).count()
    context = {
        'total_communities': total_communities,
        'high_risk': high_risk,
        'active_alerts': active_alerts,
        'predictions_today': predictions_today,
    }
    return render(request, 'disaster_manager_dashboard.html', context)


@login_required
def community_dashboard(request):
    try:
        profile = request.user.profile
        community = profile.community
    except (AttributeError, Profile.DoesNotExist):
        messages.error(request, 'You are not assigned to any community. Please contact an administrator.')
        return redirect('dashboard')
    if not community:
        messages.error(request, 'You are not assigned to any community.')
        return redirect('dashboard')
    current_risk = get_today_risk(community) or 'No Data'
    active_alerts = DailyFloodRisk.objects.filter(
        community=community,
        date=date.today(),
        flood_risk=True
    ).count()
    latest = DailyFloodRisk.objects.filter(community=community).order_by('-date').first()
    confidence = latest.confidence if latest else 0
    predictions = DailyFloodRisk.objects.filter(community=community).order_by('-date')[:5]
    context = {
        'community': community,
        'current_risk': current_risk,
        'active_alerts': active_alerts,
        'confidence': confidence,
        'predictions': predictions,
    }
    return render(request, 'community_dashboard.html', context)


@login_required
def flood_prediction(request):
    try:
        community = request.user.profile.community
    except (AttributeError, Profile.DoesNotExist):
        messages.error(request, 'You are not assigned to any community.')
        return redirect('dashboard')
    if not community:
        messages.error(request, 'You are not assigned to any community.')
        return redirect('dashboard')
    context = {
        'community': community,
        'today': date.today(),
    }
    return render(request, 'flood_prediction.html', context)


@login_required
def my_alerts(request):
    try:
        community = request.user.profile.community
    except (AttributeError, Profile.DoesNotExist):
        messages.error(request, 'You are not assigned to any community.')
        return redirect('dashboard')
    if not community:
        messages.error(request, 'You are not assigned to any community.')
        return redirect('dashboard')
    alerts = DailyFloodRisk.objects.filter(community=community).order_by('-date')
    context = {
        'community': community,
        'alerts': alerts,
        'high_count': alerts.filter(risk_level='HIGH').count(),
        'moderate_count': alerts.filter(risk_level='MODERATE').count(),
        'low_count': alerts.filter(risk_level='LOW').count(),
    }
    return render(request, 'my_alerts.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='dashboard')
def prediction_view(request):
    communities = Community.objects.all().order_by('name')
    context = {
        'communities': communities,
        'today': date.today(),
    }
    return render(request, 'prediction.html', context)


@login_required
def map_view(request):
    return render(request, 'map.html')


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='dashboard')
def alerts_view(request):
    return render(request, 'alerts.html')


@login_required
def emergency_view(request):
    emergency_contacts = [
        {'name': 'National Emergency', 'number': '112'},
        {'name': 'Police', 'number': '999'},
        {'name': 'Ambulance', 'number': '114'},
        {'name': 'Fire Brigade', 'number': '115'},
        {'name': 'Red Cross Tanzania', 'number': '0800 111 000'},
    ]
    return render(request, 'emergency.html', {'emergency_contacts': emergency_contacts})


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='dashboard')
def settings_view(request):
    return render(request, 'settings.html')


@login_required
def profile_view(request):
    return render(request, 'profile.html')


# ==================== API ENDPOINTS ====================

def api_regions(request):
    communities = list(Community.objects.values('id', 'name', 'latitude', 'longitude'))
    return JsonResponse({'communities': communities})


def api_stats(request):
    today = date.today()
    return JsonResponse({
        'total_predictions': DailyFloodRisk.objects.count(),
        'high_risk_today': DailyFloodRisk.objects.filter(date=today, flood_risk=True).count(),
        'ai_confidence': 95,
        'total_communities': Community.objects.count(),
        'active_alerts': DailyFloodRisk.objects.filter(date=today, risk_level='HIGH').count(),
    })


def api_ai_status(request):
    model_exists = os.path.exists('flood_model.pkl')
    encoder_exists = os.path.exists('community_encoder.pkl')
    return JsonResponse({
        'ai_model_trained': model_exists,
        'encoder_trained': encoder_exists,
        'status': 'ready' if model_exists and encoder_exists else 'not_ready'
    })


def api_delete_all_predictions(request):
    if request.method == 'POST' and request.user.is_superuser:
        deleted, _ = DailyFloodRisk.objects.all().delete()
        return JsonResponse({'success': True, 'deleted_count': deleted})
    return JsonResponse({'error': 'Unauthorized'}, status=403)


def api_user_predictions(request):
    predictions = DailyFloodRisk.objects.select_related('community').order_by('-date')
    data = [{
        'id': p.id,
        'community': p.community.name,
        'region': p.community.name,
        'risk_level': p.risk_level,
        'flood_risk': p.flood_risk,
        'rainfall_mm': p.rainfall_mm,
        'temperature_c': p.temperature_c,
        'humidity': p.humidity_percent,
        'humidity_percent': p.humidity_percent,
        'soil_moisture': p.soil_moisture,
        'confidence': p.confidence,
        'confidence_percent': p.confidence,
        'created_at': p.date.isoformat(),
        'date': p.date.isoformat(),
        'predicted_depth_cm': 0,
        'time_to_flood_hours': 0,
        'status': 'Active' if p.flood_risk else 'Safe',
    } for p in predictions]
    return JsonResponse({'predictions': data, 'count': len(data)})


def api_predict(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        community_name = data.get('community')
        pred_date_str = data.get('date')
        if not community_name:
            return JsonResponse({'error': 'Community name required'}, status=400)
        if pred_date_str:
            try:
                pred_date = datetime.strptime(pred_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
        else:
            pred_date = date.today()
        try:
            community = Community.objects.get(name=community_name)
        except Community.DoesNotExist:
            return JsonResponse({'error': f'Community "{community_name}" not found'}, status=404)

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, 'flood_model.pkl')
        encoder_path = os.path.join(base_dir, 'community_encoder.pkl')
        if not (os.path.exists(model_path) and os.path.exists(encoder_path)):
            return JsonResponse({
                'community': community_name,
                'risk_level': 'LOW',
                'rainfall': 0.0,
                'temperature': 28.0,
                'humidity': 70.0,
                'confidence': 85.0,
                'date': pred_date.isoformat(),
                'flood_risk': False,
                'message': 'Model not trained yet. Using default low risk.'
            })

        model = pickle.load(open(model_path, 'rb'))
        encoder = pickle.load(open(encoder_path, 'rb'))

        weather = get_daily_weather(community.latitude, community.longitude, pred_date)
        rainfall = weather['rainfall']
        temperature = weather['temperature']
        humidity = weather['humidity']
        soil_moisture = weather['soil_moisture']

        try:
            comm_enc = encoder.transform([community_name])[0]
        except Exception:
            return JsonResponse({'error': f'Community "{community_name}" not known by encoder'}, status=400)

        # ---- 9 FEATURES ----
        input_data = [[
            comm_enc, rainfall, temperature, humidity, soil_moisture,
            rainfall * humidity / 100,
            soil_moisture * rainfall,
            1 if rainfall > 50 else 0,
            humidity * soil_moisture / 100
        ]]

        # ---- PREDICT PROBABILITY (binary: Low=0, High=1) ----
        probabilities = model.predict_proba(input_data)[0]
        flood_prob = probabilities[1]   # probability of High
        confidence = round(max(probabilities) * 100, 1)

        # ---- THREE-LEVEL RISK BASED ON PROBABILITY ----
        if flood_prob >= 0.7:
            risk_level = 'HIGH'
        elif flood_prob >= 0.3:
            risk_level = 'MODERATE'
        else:
            risk_level = 'LOW'

        flood_risk = (risk_level == 'HIGH')

        # Save to database
        DailyFloodRisk.objects.update_or_create(
            community=community,
            date=pred_date,
            defaults={
                'rainfall_mm': rainfall,
                'temperature_c': temperature,
                'humidity_percent': humidity,
                'soil_moisture': soil_moisture,
                'flood_risk': flood_risk,
                'confidence': confidence,
                'risk_level': risk_level,
            }
        )

        log_system_action(
            request.user if request.user.is_authenticated else None,
            'PREDICTION',
            f"Prediction generated for {community_name} on {pred_date}: {risk_level} risk",
            request.META.get('REMOTE_ADDR')
        )

        message = f"{risk_level} flood risk for {community_name} on {pred_date.isoformat()}."
        return JsonResponse({
            'community': community_name,
            'risk_level': risk_level,
            'rainfall': round(rainfall, 1),
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'confidence': confidence,
            'date': pred_date.isoformat(),
            'flood_risk': flood_risk,
            'message': message
        })

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Prediction error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def api_train_from_database(request):
    return JsonResponse({'error': 'Use train_ai.py script from command line'}, status=501)


def api_evacuation_centers(request):
    centers = [
        {"name": "Benjamin Mkapa Stadium", "address": "Kurasini", "capacity": "5,000"},
        {"name": "Diamond Jubilee Hall", "address": "Upanga", "capacity": "2,000"},
        {"name": "Uhuru Stadium", "address": "Ilala", "capacity": "4,000"},
        {"name": "Tandale Primary School", "address": "Tandale", "capacity": "800"},
        {"name": "Kigogo Community Hall", "address": "Kigogo", "capacity": "500"},
        {"name": "Jangwani Open Ground", "address": "Jangwani", "capacity": "2,000"},
        {"name": "Manzese Polytechnic", "address": "Manzese", "capacity": "1,200"},
    ]
    return JsonResponse({'centers': centers})


def api_community_data(request):
    today = date.today()
    communities = Community.objects.all()
    data = []
    for comm in communities:
        risk = DailyFloodRisk.objects.filter(community=comm, date=today).first()
        data.append({
            'name': comm.name,
            'lat': comm.latitude,
            'lng': comm.longitude,
            'risk_level': risk.risk_level if risk else 'UNKNOWN',
            'rainfall': risk.rainfall_mm if risk else 0,
            'water_level': risk.water_level_m if hasattr(risk, 'water_level_m') else 0,
            'soil_moisture': risk.soil_moisture if risk else 0,
            'status': 'Active Alert' if risk and risk.flood_risk else 'Safe'
        })
    return JsonResponse({'communities': data})


def api_today_weather(request):
    try:
        lat = -6.7924
        lng = 39.2083
        weather = get_daily_weather(lat, lng, date.today())
        return JsonResponse({
            'temperature': weather['temperature'],
            'humidity': weather['humidity'],
            'rainfall': weather['rainfall'],
            'wind_speed': weather.get('wind_speed', 20),
            'date': date.today().isoformat()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_delete_prediction(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        pred_id = data.get('id')
        if not pred_id:
            return JsonResponse({'error': 'Prediction ID required'}, status=400)
        prediction = DailyFloodRisk.objects.get(id=pred_id)
        community_name = prediction.community.name
        pred_date = prediction.date
        risk_level = prediction.risk_level
        prediction.delete()
        log_system_action(
            request.user,
            'PREDICTION_DELETED',
            f"Prediction {pred_id} for {community_name} on {pred_date} deleted",
            request.META.get('REMOTE_ADDR')
        )
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Prediction {pred_id} ({community_name} on {pred_date}) deleted by user {request.user.username}"
        )
        return JsonResponse({
            'success': True,
            'message': f'Prediction for {community_name} on {pred_date} deleted successfully.',
            'deleted_prediction_id': pred_id,
            'community': community_name,
            'date': pred_date.isoformat(),
            'risk_level': risk_level
        })
    except DailyFloodRisk.DoesNotExist:
        return JsonResponse({'error': 'Prediction not found'}, status=404)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error deleting prediction {pred_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)