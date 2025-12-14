# urls.py
from django.urls import path
from . import views

app_name = 'hse'

urlpatterns = [
    # ========== Company URLs ==========
    path('companies/', views.company_list, name='company_list'),
    path('companies/create/', views.company_create, name='company_create'),
    path('companies/<uuid:company_id>/', views.company_detail, name='company_detail'),
    path('companies/<uuid:company_id>/edit/', views.company_edit, name='company_edit'),
    path('companies/<uuid:company_id>/toggle-active/', views.company_toggle_active, name='company_toggle_active'),

    # ========== Department URLs ==========
    path('companies/<uuid:company_id>/departments/', views.department_list, name='department_list'),
    path('companies/<uuid:company_id>/departments/create/', views.department_create, name='department_create'),
    path('companies/<uuid:company_id>/departments/<uuid:department_id>/edit/', views.department_edit, name='department_edit'),

    # ========== Member URLs ==========
    path('companies/<uuid:company_id>/members/', views.member_list, name='member_list'),
    path('companies/<uuid:company_id>/members/add/', views.member_add, name='member_add'),

    # ========== Inspection URLs ==========
    path('companies/<uuid:company_id>/inspections/', views.inspection_list, name='inspection_list'),
    path('companies/<uuid:company_id>/inspections/create/', views.inspection_create, name='inspection_create'),
    path('companies/<uuid:company_id>/inspections/<uuid:inspection_id>/', views.inspection_detail, name='inspection_detail'),
    path('companies/<uuid:company_id>/inspections/<uuid:inspection_id>/update-status/', views.inspection_update_status, name='inspection_update_status'),

    # ========== Incident URLs ==========
    path('companies/<uuid:company_id>/incidents/', views.incident_list, name='incident_list'),
    path('companies/<uuid:company_id>/incidents/create/', views.incident_create, name='incident_create'),
    path('companies/<uuid:company_id>/incidents/<uuid:incident_id>/', views.incident_detail, name='incident_detail'),

    # ========== Task URLs ==========
    path('companies/<uuid:company_id>/tasks/', views.task_list, name='task_list'),
    path('companies/<uuid:company_id>/tasks/create/', views.task_create, name='task_create'),
    path('companies/<uuid:company_id>/tasks/<uuid:task_id>/', views.task_detail, name='task_detail'),
    path('companies/<uuid:company_id>/tasks/<uuid:task_id>/update-status/', views.task_update_status, name='task_update_status'),

    # ========== Invitation URLs ==========
    path('companies/<uuid:company_id>/invitations/', views.invitation_list, name='invitation_list'),
    path('companies/<uuid:company_id>/invitations/create/', views.invitation_create, name='invitation_create'),

    # ========== Notification URLs ==========
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/count/', views.notification_count, name='notification_count'),

    # ========== HSE Report URLs ==========
    path('companies/<uuid:company_id>/hse-reports/', views.hse_report_list, name='hse_report_list'),
    path('companies/<uuid:company_id>/hse-reports/create/', views.hse_report_create, name='hse_report_create'),
    path('companies/<uuid:company_id>/hse-reports/<uuid:report_id>/', views.hse_report_detail, name='hse_report_detail'),

    # ========== Dashboard URLs ==========
    path('companies/<uuid:company_id>/dashboard/', views.dashboard, name='dashboard'),

    # ========== API URLs ==========
    path('companies/<uuid:company_id>/stats/', views.get_company_stats, name='get_company_stats'),
    path('companies/<uuid:company_id>/search/', views.search, name='search'),
     path('api/users/search/', views.search_users, name='search_users'),
    path('companies/<uuid:company_id>/invitations/', views.invitation_list, name='invitation_list'),
    path('companies/<uuid:company_id>/invitations/create/', views.invitation_create, name='invitation_create'),
    path('invitations/<str:token>/accept/', views.invitation_accept, name='invitation_accept'),
    path('invitations/<str:token>/reject/', views.invitation_reject, name='invitation_reject'),
    path('invitations/<str:token>/resend/', views.invitation_resend, name='invitation_resend'),
    path('invitations/<str:token>/cancel/', views.invitation_cancel, name='invitation_cancel'),
    path('companies/<uuid:pk>/delete/', views.company_delete, name='company_delete'),
    path('api/users/search/', views.search_users, name='search_users'),
    path('pending-invitations/', views.user_pending_invitations, name='pending_invitations'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/unread-count/', views.notification_unread_count, name='notification_unread_count'),
    path('notifications/<uuid:notification_id>/', views.notification_detail, name='notification_detail'),



       path('companies/<uuid:company_id>/trainings/',
         views.training_list,
         name='training_list'),

    path('companies/<uuid:company_id>/trainings/create/',
         views.training_create,
         name='training_create'),

    path('companies/<uuid:company_id>/trainings/<uuid:training_id>/',
         views.training_detail,
         name='training_detail'),

    path('companies/<uuid:company_id>/trainings/<uuid:training_id>/edit/',
         views.training_update,
         name='training_update'),

    path('companies/<uuid:company_id>/trainings/<uuid:training_id>/delete/',
         views.training_delete,
         name='training_delete'),

    path('companies/<uuid:company_id>/trainings/<uuid:training_id>/update-status/',
         views.training_update_status,
         name='training_update_status'),

    path('companies/<uuid:company_id>/trainings/<uuid:training_id>/register-participant/',
         views.training_register_participant,
         name='training_register_participant'),

    path('companies/<uuid:company_id>/trainings/<uuid:training_id>/update-participation/<uuid:participation_id>/',
         views.training_update_participation,
         name='training_update_participation'),


  path('ai-assistant/', views.ai_assistant, name='ai_assistant'),
     path('servicelist/',views.serviceLst,name='servicelist'),
     
     path('<uuid:company_id>/members/<uuid:member_id>/detail/',
         views.member_detail, name='member_detail'),
    path('<uuid:company_id>/members/<uuid:member_id>/change-status/',
         views.member_change_status, name='member_change_status'),
    path('<uuid:company_id>/members/<uuid:member_id>/edit/',
         views.member_edit, name='member_edit'),
    path('<uuid:company_id>/members/<uuid:member_id>/delete/',
         views.member_delete, name='member_delete'),

]