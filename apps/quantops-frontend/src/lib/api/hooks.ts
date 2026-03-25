import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch, apiMutate } from '@/lib/api/fetcher';
import { endpoints } from '@/lib/api/endpoints';
import {
  normalizeAlerts,
  normalizeApprovals,
  normalizeAuditLogs,
  normalizeCommandCenterRuntimeLatest,
  normalizeRuntimeIssueBuckets,
  normalizeCommandCenterRuntimeRuns,
  normalizeCommandCenterRuntimeDebug,
  normalizeConfig,
  normalizeCurrentUser,
  normalizeEquityHistory,
  normalizeExecutionFills,
  normalizeExecutionOrders,
  normalizeExecutionPlannerLatest,
  normalizeExecutionSummary,
  normalizeExecutionState,
  normalizeExecutionViewLatest,
  normalizeJobs,
  normalizeMonitoring,
  normalizeOverview,
  normalizePortfolioMetrics,
  normalizePortfolioOverview,
  normalizePositions,
  normalizeRisk,
  normalizeStrategies,
} from '@/lib/api/normalize';
import type {
  ActionResult,
  ApiEnvelope,
  ConfigDraft,
  CurrentUser,
  GovernanceDecision,
  MonitoringSystem,
  OverviewData,
  EquityHistoryFeed,
  ExecutionSummary,
  FeedPayload,
  ExecutionFillRow,
  ExecutionOrderRow,
  ExecutionPlannerLatest,
  ExecutionState,
  ExecutionViewLatest,
  PortfolioOverview,
  PortfolioMetrics,
  PositionFeed,
  RiskSnapshot,
  StrategyRow,
  AuditLogRow,
  CommandCenterRuntimeLatest,
  CommandCenterRuntimeRunSummary,
  CommandCenterRuntimeDebug,
  RuntimeIssueBucket,
} from '@/types/api';

function envelope<T>(data: T): ApiEnvelope<T> {
  return { data, source: 'live' };
}

function useInvalidateMutation<TVariables>(
  mutationFn: (variables: TVariables) => Promise<ApiEnvelope<ActionResult>>,
  keysToInvalidate: string[][]
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: async () => {
      await Promise.all(keysToInvalidate.map((key) => queryClient.invalidateQueries({ queryKey: key })));
    },
  });
}

export function useOverview() {
  return useQuery({
    queryKey: ['overview'],
    queryFn: async () => envelope<OverviewData>(normalizeOverview(await apiFetch<any>(endpoints.overview))),
    refetchOnMount: false,
    placeholderData: (previousData) => previousData,
  });
}
export function usePortfolioOverview(enabled = true) {
  return useQuery({
    queryKey: ['portfolio-overview'],
    queryFn: async () => envelope<PortfolioOverview>(normalizePortfolioOverview(await apiFetch<any>(endpoints.portfolioOverview))),
    enabled,
    refetchInterval: 20000,
    refetchOnMount: false,
    placeholderData: (previousData) => previousData ?? envelope<PortfolioOverview>({
      totalEquity: 0,
      balance: 0,
      usedMargin: 0,
      freeMargin: 0,
      unrealized: 0,
      grossExposure: 0,
      netExposure: 0,
      realizedPnl: 0,
      unrealizedPnl: 0,
      lastUpdated: '',
    }),
  });
}
export function usePortfolioMetrics(enabled = true) {
  return useQuery({
    queryKey: ['portfolio-metrics'],
    queryFn: async () => envelope<PortfolioMetrics>(normalizePortfolioMetrics(await apiFetch<any>(endpoints.portfolioMetrics))),
    enabled,
    refetchInterval: 20000,
    refetchOnMount: false,
    placeholderData: (previousData) => previousData ?? envelope<PortfolioMetrics>({
      fillRate: 0,
      expectedVolatility: 0,
      expectedSharpe: 0,
      lastUpdated: '',
    }),
  });
}
export function usePortfolioPositions() {
  return useQuery({
    queryKey: ['portfolio-positions'],
    queryFn: async () => envelope<PositionFeed>(normalizePositions(await apiFetch<any>(endpoints.portfolioPositions))),
    refetchInterval: 20000,
    refetchOnMount: false,
    placeholderData: (previousData) => previousData ?? envelope<PositionFeed>({ items: [] }),
  });
}
export function useRiskSnapshot(enabled = true) {
  return useQuery({
    queryKey: ['risk-snapshot'],
    queryFn: async () => envelope<RiskSnapshot>(normalizeRisk(await apiFetch<any>(endpoints.riskSnapshot))),
    enabled,
    staleTime: 30000,
    refetchInterval: 30000,
    refetchOnMount: false,
    placeholderData: (previousData) => previousData,
  });
}
export function useMonitoringSystem(enabled = true) {
  return useQuery<ApiEnvelope<MonitoringSystem>>({
    queryKey: ['monitoring-system'],
    queryFn: async () => envelope<MonitoringSystem>(normalizeMonitoring(await apiFetch<any>(endpoints.monitoringSystem))),
    enabled,
    staleTime: 30000,
    refetchInterval: 20000,
    refetchOnMount: false,
    placeholderData: (previousData) => previousData,
  });
}
export function useAlerts(enabled = true) {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: async () => envelope<any[]>(normalizeAlerts(await apiFetch<any>(endpoints.alerts))),
    enabled,
    staleTime: 30000,
    refetchInterval: 20000,
    refetchOnMount: false,
    placeholderData: (previousData) => previousData ?? envelope<any[]>([]),
  });
}
export function useSchedulerJobs(enabled = true) {
  return useQuery({
    queryKey: ['scheduler-jobs'],
    queryFn: async () => envelope<any[]>(normalizeJobs(await apiFetch<any>(endpoints.schedulerJobs))),
    enabled,
    refetchInterval: 20000,
    placeholderData: (previousData) => previousData ?? envelope<any[]>([]),
  });
}

export function useEquityHistory(enabled = true) {
  return useQuery({
    queryKey: ['equity-history'],
    queryFn: async () => envelope<EquityHistoryFeed>(normalizeEquityHistory(await apiFetch<any>(endpoints.equityHistory))),
    enabled,
    refetchInterval: 30000,
    placeholderData: (previousData) => previousData ?? envelope<EquityHistoryFeed>({ items: [] }),
  });
}
export function useExecutionSummary() {
  return useQuery({
    queryKey: ['execution-summary'],
    queryFn: async () => envelope<ExecutionSummary>(normalizeExecutionSummary(await apiFetch<any>(endpoints.executionSummary))),
    refetchInterval: 15000,
    retry: 1,
    placeholderData: (previousData) => previousData,
  });
}
export function useExecutionLatest(enabled = true, limit = 100) {
  return useQuery({
    queryKey: ['execution-latest', limit],
    queryFn: async () => envelope<FeedPayload<ExecutionFillRow>>(normalizeExecutionFills(await apiFetch<any>(`${endpoints.executionLatest}?limit=${limit}`))),
    enabled,
    refetchInterval: 15000,
    placeholderData: (previousData) => previousData ?? envelope<FeedPayload<ExecutionFillRow>>({ items: [] }),
  });
}
export function useExecutionPlannerLatest(enabled = true) {
  return useQuery({
    queryKey: ['execution-planner-latest'],
    queryFn: async () => envelope<ExecutionPlannerLatest>(normalizeExecutionPlannerLatest(await apiFetch<any>(endpoints.executionPlannerLatest))),
    enabled,
    refetchInterval: 15000,
    placeholderData: (previousData) => previousData,
  });
}
export function useExecutionViewLatest(enabled = true) {
  return useQuery({
    queryKey: ['execution-view-latest'],
    queryFn: async () => envelope<ExecutionViewLatest>(normalizeExecutionViewLatest(await apiFetch<any>(endpoints.executionViewLatest))),
    enabled,
    refetchInterval: 15000,
    placeholderData: (previousData) => previousData,
  });
}
export function useExecutionOrders(enabled = true, limit = 100) {
  return useQuery({
    queryKey: ['execution-orders', limit],
    queryFn: async () => envelope<FeedPayload<ExecutionOrderRow>>(normalizeExecutionOrders(await apiFetch<any>(`${endpoints.executionOrders}?limit=${limit}`))),
    enabled,
    refetchInterval: 15000,
    placeholderData: (previousData) => previousData ?? envelope<FeedPayload<ExecutionOrderRow>>({ items: [] }),
  });
}
export function useExecutionStateLatest(enabled = true) {
  return useQuery({
    queryKey: ['execution-state-latest'],
    queryFn: async () => envelope<ExecutionState>(normalizeExecutionState(await apiFetch<any>(endpoints.executionStateLatest))),
    enabled,
    refetchInterval: 15000,
    placeholderData: (previousData) => previousData,
  });
}
export function useCommandCenterRuntimeLatest(enabled = true) {
  return useQuery({
    queryKey: ['command-center-runtime-latest'],
    queryFn: async () => envelope<CommandCenterRuntimeLatest>(normalizeCommandCenterRuntimeLatest(await apiFetch<any>(endpoints.commandCenterRuntimeLatest))),
    enabled,
    refetchInterval: 30000,
    placeholderData: (previousData) => previousData,
  });
}
export function useCommandCenterRuntimeRuns(filters?: {
  limit?: number;
  windowMinutes?: number;
  operatorState?: string;
  bridgeState?: string;
  issueCode?: string;
  reasonCode?: string;
  blockingComponent?: string;
  degraded?: boolean;
  eventChainComplete?: boolean;
  artifactAvailable?: boolean;
}, enabled = true) {
  const params = new URLSearchParams();
  params.set('limit', String(filters?.limit ?? 25));
  params.set('window_minutes', String(filters?.windowMinutes ?? 5));
  if (filters?.operatorState) params.set('operator_state', filters.operatorState);
  if (filters?.bridgeState) params.set('bridge_state', filters.bridgeState);
  if (filters?.issueCode) params.set('issue_code', filters.issueCode);
  if (filters?.reasonCode) params.set('reason_code', filters.reasonCode);
  if (filters?.blockingComponent) params.set('blocking_component', filters.blockingComponent);
  if (filters?.degraded != null) params.set('degraded', String(filters.degraded));
  if (filters?.eventChainComplete != null) params.set('event_chain_complete', String(filters.eventChainComplete));
  if (filters?.artifactAvailable != null) params.set('artifact_available', String(filters.artifactAvailable));
  const url = `${endpoints.commandCenterRuntimeRuns}?${params.toString()}`;

  return useQuery({
    queryKey: ['command-center-runtime-runs', filters?.limit ?? 25, filters?.windowMinutes ?? 5, filters?.operatorState ?? '', filters?.bridgeState ?? '', filters?.issueCode ?? '', filters?.reasonCode ?? '', filters?.blockingComponent ?? '', filters?.degraded ?? 'any', filters?.eventChainComplete ?? 'any', filters?.artifactAvailable ?? 'any'],
    queryFn: async () => envelope<FeedPayload<CommandCenterRuntimeRunSummary>>(normalizeCommandCenterRuntimeRuns(await apiFetch<any>(url))),
    enabled,
    refetchOnMount: false,
    placeholderData: (previousData) => previousData ?? envelope<FeedPayload<CommandCenterRuntimeRunSummary>>({ items: [] }),
  });
}
export function useCommandCenterRuntimeIssues(limit = 25, enabled = true, windowMinutes = 5) {
  return useQuery({
    queryKey: ['command-center-runtime-issues', limit, windowMinutes],
    queryFn: async () => envelope<FeedPayload<RuntimeIssueBucket>>(normalizeRuntimeIssueBuckets(await apiFetch<any>(`${endpoints.commandCenterRuntimeIssues}?limit=${limit}&window_minutes=${windowMinutes}`))),
    enabled,
    refetchOnMount: false,
    placeholderData: (previousData) => previousData ?? envelope<FeedPayload<RuntimeIssueBucket>>({ items: [] }),
  });
}
export function useCommandCenterRuntimeDebug(runId: string) {
  return useQuery({
    queryKey: ['command-center-runtime-debug', runId],
    queryFn: async () => envelope<CommandCenterRuntimeDebug>(normalizeCommandCenterRuntimeDebug(await apiFetch<any>(endpoints.commandCenterRuntimeDebugByRun(runId)))),
    enabled: Boolean(runId),
    refetchInterval: 15000,
    placeholderData: (previousData) => previousData,
  });
}
export function useReviewRuntimeRun() {
  return useInvalidateMutation<{ runId: string; reviewStatus: string; acknowledged?: boolean; operatorNote?: string }>(
    ({ runId, reviewStatus, acknowledged, operatorNote }) =>
      apiMutate<ActionResult>(endpoints.commandCenterRuntimeRunReview(runId), 'POST', {
        review_status: reviewStatus,
        acknowledged,
        operator_note: operatorNote,
      }),
    [['command-center-runtime-runs'], ['command-center-runtime-issues'], ['command-center-runtime-debug']]
  );
}
export function useAcknowledgeRuntimeIssue() {
  return useInvalidateMutation<{ diagnosisCode: string; note?: string }>(
    ({ diagnosisCode, note }) =>
      apiMutate<ActionResult>(endpoints.commandCenterRuntimeIssueAcknowledge(diagnosisCode), 'POST', {
        note,
      }),
    [['command-center-runtime-runs'], ['command-center-runtime-issues']]
  );
}
export function useStrategyRegistry() {
  return useQuery({
    queryKey: ['strategy-registry'],
    queryFn: async () => envelope<StrategyRow[]>(normalizeStrategies(await apiFetch<any>(endpoints.strategyRegistry)) as StrategyRow[]),
    refetchInterval: 15000,
    placeholderData: (previousData) => previousData ?? envelope<StrategyRow[]>([]),
  });
}
export function useGovernanceApprovals() {
  return useQuery({
    queryKey: ['governance-approvals'],
    queryFn: async () => envelope<GovernanceDecision[]>(normalizeApprovals(await apiFetch<any>(endpoints.governanceApprovals)) as GovernanceDecision[]),
    refetchInterval: 15000,
    placeholderData: (previousData) => previousData ?? envelope<GovernanceDecision[]>([]),
  });
}
export function useConfigCurrent() {
  return useQuery({
    queryKey: ['config-current'],
    queryFn: async () => envelope<ConfigDraft>(normalizeConfig(await apiFetch<any>(endpoints.configCurrent)) as ConfigDraft),
    refetchInterval: 30000,
    placeholderData: (previousData) => previousData ?? envelope<ConfigDraft>({
      version: 'local-default',
      schedulerCadenceSec: 60,
      riskLimit: 0.1,
      monitoringThreshold: 0.9,
      executionMode: 'paper',
    }),
  });
}
export function useCurrentUser() {
  return useQuery({
    queryKey: ['current-user'],
    queryFn: async () => envelope<CurrentUser>(normalizeCurrentUser(await apiFetch<any>(endpoints.currentUser)) as CurrentUser),
    staleTime: 60000,
    placeholderData: (previousData) => previousData ?? envelope<CurrentUser>({
      id: 'local-viewer',
      name: 'Local Viewer',
      role: 'viewer',
    }),
  });
}
export function useAuditLogs() {
  return useQuery({
    queryKey: ['audit-logs'],
    queryFn: async () => envelope<AuditLogRow[]>(normalizeAuditLogs(await apiFetch<any>(endpoints.auditLogs)) as AuditLogRow[]),
    refetchInterval: 15000,
    placeholderData: (previousData) => previousData ?? envelope<AuditLogRow[]>([]),
  });
}

export function useAcknowledgeAlert() {
  return useInvalidateMutation<string>((id) => apiMutate<ActionResult>(endpoints.alertAcknowledge(id)), [['alerts'], ['overview'], ['audit-logs']]);
}
export function useRunSchedulerJob() {
  return useInvalidateMutation<string>((name) => apiMutate<ActionResult>(endpoints.schedulerRun(name)), [['scheduler-jobs'], ['overview'], ['audit-logs']]);
}
export function usePauseSchedulerJob() {
  return useInvalidateMutation<string>((name) => apiMutate<ActionResult>(endpoints.schedulerPause(name)), [['scheduler-jobs'], ['audit-logs']]);
}
export function useResumeSchedulerJob() {
  return useInvalidateMutation<string>((name) => apiMutate<ActionResult>(endpoints.schedulerResume(name)), [['scheduler-jobs'], ['audit-logs']]);
}
export function useStartStrategy() {
  return useInvalidateMutation<string>((id) => apiMutate<ActionResult>(endpoints.commandCenterStrategyStart, 'POST', { strategy_id: id }), [['strategy-registry'], ['overview'], ['audit-logs'], ['risk-snapshot']]);
}
export function useStopStrategy() {
  return useInvalidateMutation<string>((id) => apiMutate<ActionResult>(endpoints.commandCenterStrategyStop, 'POST', { strategy_id: id }), [['strategy-registry'], ['overview'], ['audit-logs'], ['risk-snapshot']]);
}
export function useUpdateStrategyRiskBudget() {
  return useInvalidateMutation<{ strategyId: string; riskBudget: number; note?: string }>(
    ({ strategyId, riskBudget, note }) => apiMutate<ActionResult>(endpoints.commandCenterStrategyRisk, 'POST', { strategy_id: strategyId, risk_budget: riskBudget, note }),
    [['strategy-registry'], ['risk-snapshot'], ['audit-logs']]
  );
}
export function usePauseTrading() {
  return useInvalidateMutation<{ note?: string }>((payload) => apiMutate<ActionResult>(endpoints.commandCenterRiskPause, 'POST', payload), [['risk-snapshot'], ['overview'], ['audit-logs']]);
}
export function useResumeTrading() {
  return useInvalidateMutation<{ note?: string }>((payload) => apiMutate<ActionResult>(endpoints.commandCenterRiskResume, 'POST', payload), [['risk-snapshot'], ['overview'], ['audit-logs']]);
}
export function useKillSwitch() {
  return useInvalidateMutation<{ note?: string }>((payload) => apiMutate<ActionResult>(endpoints.commandCenterRiskKillSwitch, 'POST', payload), [['risk-snapshot'], ['overview'], ['audit-logs']]);
}
export function useApproveGovernance() {
  return useInvalidateMutation<string>((id) => apiMutate<ActionResult>(endpoints.governanceApprove(id)), [['governance-approvals'], ['audit-logs']]);
}
export function useRejectGovernance() {
  return useInvalidateMutation<string>((id) => apiMutate<ActionResult>(endpoints.governanceReject(id)), [['governance-approvals'], ['audit-logs']]);
}
export function useSaveConfigDraft() {
  return useInvalidateMutation<Partial<ConfigDraft>>((payload) => apiMutate<ActionResult>(endpoints.configDraftSave, 'POST', payload), [['config-current'], ['audit-logs']]);
}

export const usePositions = usePortfolioPositions;
