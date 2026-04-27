import type { ConversationSnapshot, MarketQuote } from "../../shared/types";
import type { UiCopy } from "../../shared/i18n";

interface AnalysisPanelProps {
  copy: UiCopy["analysis"];
  snapshot: ConversationSnapshot | null;
}

function formatPrice(quote: MarketQuote): string {
  const maximumFractionDigits = quote.currency === "KRW" ? 0 : 2;
  return `${quote.lastPrice.toLocaleString("en-US", { maximumFractionDigits })} ${quote.currency}`;
}

function statusText(snapshot: ConversationSnapshot | null, copy: UiCopy["analysis"]): string {
  if (!snapshot) {
    return copy.waiting;
  }
  if (snapshot.status === "needs_input") {
    return snapshot.missingInputs.includes("horizon") ? copy.horizonRequired : copy.stockRequired;
  }
  return copy.requestRecorded;
}

export function AnalysisPanel({ copy, snapshot }: AnalysisPanelProps) {
  const quote = snapshot?.marketSnapshot ?? null;

  return (
    <section className="panel" aria-label={copy.aria}>
      <div className="panel-heading">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h2>{copy.title}</h2>
      </div>

      <div className="snapshot-card">
        <span className="snapshot-status">{statusText(snapshot, copy)}</span>
        {quote ? (
          <>
            <strong>{quote.name}</strong>
            <dl className="quote-grid">
              <div>
                <dt>{copy.symbol}</dt>
                <dd>{quote.symbol}</dd>
              </div>
              <div>
                <dt>{copy.price}</dt>
                <dd>{formatPrice(quote)}</dd>
              </div>
              <div>
                <dt>{copy.exchange}</dt>
                <dd>{quote.exchange}</dd>
              </div>
              <div>
                <dt>{copy.asOf}</dt>
                <dd>{quote.asOfAt}</dd>
              </div>
            </dl>
          </>
        ) : (
          <p className="muted-copy">{copy.noSnapshot}</p>
        )}
      </div>

      <div className="probability-pending">
        <span>{copy.buy}</span>
        <span>{copy.hold}</span>
        <span>{copy.sell}</span>
        <strong>{copy.pending}</strong>
      </div>
    </section>
  );
}
