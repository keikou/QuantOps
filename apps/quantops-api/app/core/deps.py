from __future__ import annotations

from functools import lru_cache

from app.clients.v12_client import V12Client
from app.core.config import get_settings
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.governance_repository import GovernanceRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.monitoring_repository import MonitoringRepository
from app.repositories.duckdb import DuckDBConnectionFactory
from app.repositories.risk_repository import RiskRepository
from app.repositories.scheduler_repository import SchedulerRepository
from app.services.admin_service import AdminService
from app.services.alert_service import AlertService
from app.services.analytics_service import AnalyticsService
from app.services.approval_service import ApprovalService
from app.services.control_service import ControlService
from app.services.governance_service import GovernanceService
from app.services.incident_service import IncidentService
from app.services.monitoring_service import MonitoringService
from app.services.dashboard_service import DashboardService
from app.services.portfolio_service import PortfolioService
from app.services.risk_service import RiskService
from app.services.scheduler_service import SchedulerService
from app.services.command_center_service import CommandCenterService
from app.services.event_stream_service import EventStreamService
from app.services.notification_service import NotificationService


@lru_cache(maxsize=1)
def get_db_factory() -> DuckDBConnectionFactory:
    settings = get_settings()
    return DuckDBConnectionFactory(settings.db_path)


@lru_cache(maxsize=1)
def get_v12_client() -> V12Client:
    settings = get_settings()
    return V12Client(base_url=settings.v12_base_url, timeout=settings.v12_timeout_seconds, mock_mode=settings.v12_mock_mode)


def get_scheduler_repository() -> SchedulerRepository:
    return SchedulerRepository(get_db_factory())


def get_risk_repository() -> RiskRepository:
    return RiskRepository(get_db_factory())


def get_audit_repository() -> AuditRepository:
    return AuditRepository(get_db_factory())


def get_analytics_repository() -> AnalyticsRepository:
    return AnalyticsRepository(get_db_factory())


@lru_cache(maxsize=1)
def get_dashboard_service() -> DashboardService:
    return DashboardService(get_v12_client(), get_scheduler_repository(), get_alert_service())


def get_portfolio_service() -> PortfolioService:
    return PortfolioService(get_v12_client())


def get_scheduler_service() -> SchedulerService:
    return SchedulerService(get_scheduler_repository(), get_audit_repository(), get_risk_repository())


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService(get_v12_client(), get_analytics_repository())


def get_control_service() -> ControlService:
    return ControlService(get_v12_client(), get_audit_repository(), get_analytics_repository(), get_risk_repository())


@lru_cache(maxsize=1)
def get_risk_service() -> RiskService:
    return RiskService(get_v12_client(), get_risk_repository())


def get_monitoring_repository() -> MonitoringRepository:
    return MonitoringRepository(get_db_factory())

def get_alert_repository() -> AlertRepository:
    return AlertRepository(get_db_factory())

def get_governance_repository() -> GovernanceRepository:
    return GovernanceRepository(get_db_factory())

def get_approval_repository() -> ApprovalRepository:
    return ApprovalRepository(get_db_factory())

def get_incident_repository() -> IncidentRepository:
    return IncidentRepository(get_db_factory())

@lru_cache(maxsize=1)
def get_monitoring_service() -> MonitoringService:
    return MonitoringService(get_v12_client(), get_monitoring_repository())

def get_alert_service() -> AlertService:
    return AlertService(get_alert_repository(), get_audit_repository(), get_risk_repository(), get_monitoring_repository())

def get_governance_service() -> GovernanceService:
    return GovernanceService(get_v12_client(), get_governance_repository())

def get_approval_service() -> ApprovalService:
    return ApprovalService(get_approval_repository(), get_audit_repository())

def get_incident_service() -> IncidentService:
    return IncidentService(get_incident_repository(), get_audit_repository())

def get_admin_service() -> AdminService:
    return AdminService(get_audit_repository())



def get_notification_service() -> NotificationService:
    return NotificationService(get_audit_repository())

def get_command_center_service() -> CommandCenterService:
    return CommandCenterService(
        get_v12_client(),
        get_dashboard_service(),
        get_portfolio_service(),
        get_risk_service(),
        get_analytics_service(),
        get_monitoring_service(),
        get_alert_service(),
        get_scheduler_service(),
        get_control_service(),
        get_analytics_repository(),
        get_audit_repository(),
        get_risk_repository(),
        get_notification_service(),
    )


def get_event_stream_service() -> EventStreamService:
    return EventStreamService(get_command_center_service())
