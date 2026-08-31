"""Business orchestration for deterministic Data Chat queries."""

from __future__ import annotations

from app.core.config import get_settings
from app.models.dataset import Dataset
from app.schemas.data_chat import DataChatQueryPlan
from app.services.analysis_engine import AnalysisEngine
from app.services.field_mapping_override_service import FieldMappingOverrideService
from app.services.metrics_service import MetricsService
from app.services.data_chat.metric_query_engine import MetricQueryEngine
from app.services.data_chat.question_interpreter import (
    LLMQuestionInterpreter,
    QuestionClarificationRequired,
    QueryPlanParseError,
    RuleBasedQuestionInterpreter,
)


class DataChatServiceError(ValueError):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class DataChatService:
    def __init__(
        self,
        metrics_service: MetricsService | None = None,
        field_mapping_service: FieldMappingOverrideService | None = None,
        rule_interpreter: RuleBasedQuestionInterpreter | None = None,
        llm_interpreter: LLMQuestionInterpreter | None = None,
        metric_query_engine: MetricQueryEngine | None = None,
        analysis_engine: AnalysisEngine | None = None,
    ) -> None:
        self._metrics_service = metrics_service or MetricsService()
        self._field_mapping_service = field_mapping_service or FieldMappingOverrideService()
        self._rule_interpreter = rule_interpreter or RuleBasedQuestionInterpreter()
        self._llm_interpreter = llm_interpreter or LLMQuestionInterpreter()
        self._metric_query_engine = metric_query_engine or MetricQueryEngine()
        self._analysis_engine = analysis_engine or AnalysisEngine()

    def query(self, db, current_user, dataset_id: int, question: str) -> dict[str, object]:
        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise DataChatServiceError(404, "数据集不存在")
        if dataset.owner_id != current_user.id:
            raise DataChatServiceError(403, "无权查询此数据集")

        try:
            frame = self._metrics_service.load_cleaned_frame(db, dataset)
        except ValueError as error:
            raise DataChatServiceError(400, str(error)) from error
        try:
            overrides = self._field_mapping_service.get_overrides(db, dataset.id)
            _mapped_frame, context = self._analysis_engine.prepare_context(
                frame, field_overrides=overrides
            )
        except ValueError as error:
            raise DataChatServiceError(400, str(error)) from error
        if context["selected_module"]["id"] != "order":
            raise DataChatServiceError(400, "当前数据集暂不支持订单数据问答")

        try:
            plan, interpreter_mode = self._resolve_plan(question, frame, overrides)
        except QuestionClarificationRequired as error:
            raise DataChatServiceError(400, str(error)) from error
        except QueryPlanParseError as error:
            raise DataChatServiceError(400, str(error)) from error

        result = self._metric_query_engine.query(frame, plan, field_overrides=overrides)
        return {
            "question": question,
            "dataset": {"id": dataset.id, "original_filename": dataset.original_filename},
            "query_plan": plan.model_dump(mode="json"),
            "result": result,
            "interpreter_mode": interpreter_mode,
        }

    def _resolve_plan(
        self, question: str, frame, overrides: dict[str, str]
    ) -> tuple[DataChatQueryPlan, str]:
        plan = self._rule_interpreter.interpret(question, frame, field_overrides=overrides)
        if plan is not None:
            return plan, "rule"
        settings = get_settings()
        if settings.llm_provider != "deepseek" or not settings.llm_api_key:
            raise QueryPlanParseError("当前暂不支持该类型的数据查询。")
        return self._llm_interpreter.interpret(question), "llm"
