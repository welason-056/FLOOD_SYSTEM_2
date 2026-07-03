from django.contrib import admin
from django.urls import path
from prediction import views   # Import views from the prediction app

urlpatterns = [
    # ==================== Admin ====================
    path('admin/', admin.site.urls),

    # ==================== Frontend Pages ====================
    path('', views.home_page, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('prediction/', views.prediction_view, name='prediction'),
    path('map/', views.map_view, name='map'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('emergency/', views.emergency_view, name='emergency'),
    path('settings/', views.settings_view, name='settings'),
    path('profile/', views.profile_view, name='profile'),

    # ==================== History & Reports (Staff only) ====================
    path('history/', views.history_view, name='history'),
    path('reports/', views.reports_view, name='reports'),

    # ==================== Manager Profile & Admin Pages ====================
    path('manager-profile/', views.manager_profile, name='manager_profile'),
    path('alerts-management/', views.alerts_management, name='alerts_management'),
    path('communities/', views.communities_view, name='communities'),

    # ==================== Backup & Restore (Superuser only) ====================
    path('backup-restore/', views.backup_restore_view, name='backup_restore'),
    path('api/create-backup/', views.create_backup, name='create_backup'),
    path('backup/download/<str:filename>/', views.download_backup, name='download_backup'),
    path('backup/restore/<str:filename>/', views.restore_backup, name='restore_backup'),
    path('backup/delete/<str:filename>/', views.delete_backup, name='delete_backup'),

    # ==================== System Logs (Superuser only) ====================
    path('system-logs/', views.system_logs_view, name='system_logs'),

    # ==================== Community Member Pages ====================
    path('flood-prediction/', views.flood_prediction, name='flood_prediction'),
    path('my-alerts/', views.my_alerts, name='my_alerts'),

    # ==================== Role‑Based Dashboards ====================
    path('disaster-dashboard/', views.disaster_manager_dashboard, name='disaster_manager_dashboard'),
    path('community-dashboard/', views.community_dashboard, name='community_dashboard'),

    # ==================== API Endpoints ====================
    path('api/regions/', views.api_regions, name='api_regions'),
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/ai-status/', views.api_ai_status, name='api_ai_status'),
    path('api/delete-all-predictions/', views.api_delete_all_predictions, name='delete_all_predictions'),
    path('api/user-predictions/', views.api_user_predictions, name='api_user_predictions'),
    path('api/predict/', views.api_predict, name='api_predict'),
    path('api/train-from-database/', views.api_train_from_database, name='api_train_from_database'),
    path('api/evacuation-centers/', views.api_evacuation_centers, name='api_evacuation_centers'),
    path('api/community-data/', views.api_community_data, name='api_community_data'),
    path('api/delete-prediction/', views.api_delete_prediction, name='api_delete_prediction'),
    path('api/weather/today/', views.api_today_weather, name='api_today_weather'),
    path('api/send-warning/', views.api_send_warning, name='api_send_warning'),
    path('api/resolve-alert/', views.api_resolve_alert, name='api_resolve_alert'),
    path('api/update-profile/', views.api_update_profile, name='api_update_profile'),
    path('api/nearest-community/', views.api_nearest_community, name='api_nearest_community'),
    path('api/clear-logs/', views.api_clear_logs, name='api_clear_logs'),
]