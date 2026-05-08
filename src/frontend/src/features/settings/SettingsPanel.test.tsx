import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { SettingsPanel } from "./SettingsPanel";
import { uiCopy } from "../../shared/i18n";

describe("SettingsPanel", () => {
  it("saves analysis defaults", () => {
    const onSave = vi.fn();

    render(
      <SettingsPanel
        copy={uiCopy.en.settings}
        isSaving={false}
        onSave={onSave}
        settings={{
          analysisMode: "quick",
          defaultMarket: "KR",
          defaultHorizon: null,
        }}
      />,
    );

    fireEvent.change(screen.getByLabelText("Analysis mode"), { target: { value: "deep" } });
    fireEvent.change(screen.getByLabelText("Default market"), { target: { value: "US" } });
    fireEvent.change(screen.getByLabelText("Default horizon"), { target: { value: "swing" } });
    fireEvent.click(screen.getByRole("button", { name: "Save settings" }));

    expect(onSave).toHaveBeenCalledWith({
      analysisMode: "deep",
      defaultMarket: "US",
      defaultHorizon: "swing",
    });
  });

  it("renders save errors from the app shell", () => {
    render(
      <SettingsPanel
        copy={uiCopy.en.settings}
        errorMessage="Settings could not be saved."
        isSaving={false}
        onSave={vi.fn()}
        settings={{
          analysisMode: "quick",
          defaultMarket: "KR",
          defaultHorizon: null,
        }}
      />,
    );

    expect(screen.getByText("Settings could not be saved.")).toBeInTheDocument();
  });
});
