import type {
  AnalysisResult,
  AnalysisSourceDocument,
  ConversationSnapshot,
} from "../../shared/types";
import type { UiCopy } from "../../shared/i18n";
import { MarketChart } from "./MarketChart";

interface AnalysisPanelProps {
  copy: UiCopy["analysis"];
  snapshot: ConversationSnapshot | null;
}

function statusText(snapshot: ConversationSnapshot | null, copy: UiCopy["analysis"]): string {
  if (!snapshot) {
    return copy.waiting;
  }
  if (snapshot.status === "needs_input") {
    return snapshot.missingInputs.includes("horizon") ? copy.horizonRequired : copy.stockRequired;
  }
  if (snapshot.status === "analysis_completed") {
    return copy.analysisCompleted;
  }
  if (snapshot.status === "setup_needed") {
    return copy.setupNeeded;
  }
  if (snapshot.status === "provider_error") {
    return copy.providerError;
  }
  return copy.requestRecorded;
}

function sourceStatusText(
  document: AnalysisSourceDocument,
  analysis: AnalysisResult,
  copy: UiCopy["analysis"],
): string {
  if (!document.includedInAnalysis) {
    return copy.excludedSource;
  }
  return analysis.sourceAudit.promptDocumentIds.includes(document.id)
    ? copy.usedInPrompt
    : copy.includedSource;
}

function SourceAudit({
  analysis,
  copy,
}: {
  analysis: AnalysisResult | null | undefined;
  copy: UiCopy["analysis"];
}) {
  if (!analysis) {
    return (
      <section className="source-audit" aria-label={copy.sourceAudit}>
        <h3>{copy.sourceAudit}</h3>
        <p className="muted-copy">{copy.noSourceAudit}</p>
      </section>
    );
  }

  return (
    <section className="source-audit" aria-label={copy.sourceAudit}>
      <div className="source-audit-heading">
        <h3>{copy.sourceAudit}</h3>
        <div className="source-audit-counts" aria-label={copy.sourceAudit}>
          <span>{`${analysis.includedDocumentCount} ${copy.included}`}</span>
          <span>{`${analysis.excludedDocumentCount} ${copy.excluded}`}</span>
        </div>
      </div>

      {analysis.sourceAudit.sourceWarnings.length > 0 ? (
        <div className="source-warning-list" aria-label={copy.sourceWarnings}>
          {analysis.sourceAudit.sourceWarnings.map((warning) => (
            <span key={warning}>{warning}</span>
          ))}
        </div>
      ) : null}

      <ul className="source-audit-list">
        {analysis.sourceDocuments.map((document) => (
          <li key={document.id}>
            <div className="source-audit-row">
              <span
                className={
                  document.includedInAnalysis
                    ? "source-state source-state-included"
                    : "source-state source-state-excluded"
                }
              >
                {sourceStatusText(document, analysis, copy)}
              </span>
              <strong>{document.title}</strong>
            </div>
            <dl className="source-audit-meta">
              <div>
                <dt>{document.sourceName}</dt>
                <dd>{document.publishedAt}</dd>
              </div>
              {document.exclusionReason ? (
                <div>
                  <dt>{copy.excluded}</dt>
                  <dd>{document.exclusionReason}</dd>
                </div>
              ) : null}
            </dl>
          </li>
        ))}
      </ul>
    </section>
  );
}

function formatProbability(value: number): string {
  return `${value.toFixed(1)}%`;
}

function formatSignedPercent(value: number): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`;
}

function ProbabilitySummary({
  analysis,
  copy,
}: {
  analysis: AnalysisResult | null | undefined;
  copy: UiCopy["analysis"];
}) {
  const score = analysis?.scoreResult ?? null;
  if (!score || score.status !== "scored") {
    return (
      <div className="probability-pending">
        <span>{copy.buy}</span>
        <span>{copy.hold}</span>
        <span>{copy.sell}</span>
        <strong>{copy.pending}</strong>
      </div>
    );
  }

  return (
    <div className="probability-summary" aria-label={copy.probabilities}>
      <div>
        <span>{copy.buy}</span>
        <strong>{formatProbability(score.buyProbability)}</strong>
      </div>
      <div>
        <span>{copy.hold}</span>
        <strong>{formatProbability(score.holdProbability)}</strong>
      </div>
      <div>
        <span>{copy.sell}</span>
        <strong>{formatProbability(score.sellProbability)}</strong>
      </div>
      <p>{`${copy.confidence}: ${score.confidenceScore.toFixed(2)}`}</p>
      <p>
        {`${copy.expectedRange}: ${formatSignedPercent(score.expectedReturnMinPct)} to `}
        {`${formatSignedPercent(score.expectedReturnMaxPct)} · `}
        {`${copy.downsideRisk}: ${formatProbability(score.downsideProbability)}`}
      </p>
      <p>
        {`${copy.similarEvents}: ${score.similarEventSampleCount} samples · `}
        {`${formatProbability(score.similarEventWinRate)} win rate · `}
        {`${formatSignedPercent(score.similarEventMedianReturnPct)} median`}
      </p>
      {score.confidenceFactors?.length ? (
        <p>{`${copy.confidenceFactors}: ${score.confidenceFactors.join(", ")}`}</p>
      ) : null}
    </div>
  );
}

function OperationalState({
  analysis,
  copy,
}: {
  analysis: AnalysisResult | null | undefined;
  copy: UiCopy["analysis"];
}) {
  if (!analysis || (!analysis.provider && !analysis.model)) {
    return null;
  }

  return (
    <div className="analysis-operational-state" aria-label="Analysis provider state">
      {analysis.provider ? <span>{`${copy.provider}: ${analysis.provider}`}</span> : null}
      {analysis.model ? <span>{`${copy.model}: ${analysis.model}`}</span> : null}
      {analysis.providerErrorCode ? <span>{analysis.providerErrorCode}</span> : null}
    </div>
  );
}

export function AnalysisPanel({ copy, snapshot }: AnalysisPanelProps) {
  const quote = snapshot?.marketSnapshot ?? null;
  const analysis = snapshot?.analysisResult ?? null;

  return (
    <section className="panel" aria-label={copy.aria}>
      <div className="panel-heading">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h2>{copy.title}</h2>
      </div>

      <div className="snapshot-card">
        <span className="snapshot-status">{statusText(snapshot, copy)}</span>
        {quote ? (
          <MarketChart quote={quote} />
        ) : (
          <p className="muted-copy">{copy.noSnapshot}</p>
        )}
      </div>

      <ProbabilitySummary analysis={analysis} copy={copy} />

      <OperationalState analysis={analysis} copy={copy} />

      <SourceAudit analysis={analysis} copy={copy} />
    </section>
  );
}
