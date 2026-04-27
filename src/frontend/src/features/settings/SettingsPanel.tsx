import { FormEvent, useEffect, useState } from "react";

import type { AppSettings, HorizonType } from "../../shared/types";
import type { UiCopy } from "../../shared/i18n";

interface SettingsPanelProps {
  copy: UiCopy["settings"];
  errorMessage?: string | null;
  isSaving: boolean;
  settings: AppSettings;
  onSave: (settings: AppSettings) => void;
}

const horizonOptions: Array<{ key: HorizonType | "none"; value: HorizonType | "" }> = [
  { key: "none", value: "" },
  { key: "intraday", value: "intraday" },
  { key: "swing", value: "swing" },
  { key: "long_term", value: "long_term" },
];

export function SettingsPanel({
  copy,
  errorMessage = null,
  isSaving,
  onSave,
  settings,
}: SettingsPanelProps) {
  const [draft, setDraft] = useState<AppSettings>(settings);

  useEffect(() => {
    setDraft(settings);
  }, [settings]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSave(draft);
  }

  return (
    <section className="panel" aria-label={copy.aria}>
      <div className="panel-heading">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h2>{copy.title}</h2>
      </div>
      <form className="settings-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>{copy.analysisMode}</span>
          <select
            aria-label={copy.analysisMode}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                analysisMode: event.target.value as AppSettings["analysisMode"],
              }))
            }
            value={draft.analysisMode}
          >
            <option value="quick">{copy.modes.quick}</option>
            <option value="deep">{copy.modes.deep}</option>
          </select>
        </label>
        <label className="field">
          <span>{copy.defaultMarket}</span>
          <select
            aria-label={copy.defaultMarket}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                defaultMarket: event.target.value as AppSettings["defaultMarket"],
              }))
            }
            value={draft.defaultMarket}
          >
            <option value="KR">KR</option>
            <option value="US">US</option>
          </select>
        </label>
        <label className="field">
          <span>{copy.defaultHorizon}</span>
          <select
            aria-label={copy.defaultHorizon}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                defaultHorizon: event.target.value ? (event.target.value as HorizonType) : null,
              }))
            }
            value={draft.defaultHorizon ?? ""}
          >
            {horizonOptions.map((option) => (
              <option key={option.value || "none"} value={option.value}>
                {copy.horizons[option.key]}
              </option>
            ))}
          </select>
        </label>
        <button disabled={isSaving} type="submit">
          {copy.save}
        </button>
      </form>
      {errorMessage ? <p className="inline-error">{errorMessage}</p> : null}
    </section>
  );
}
