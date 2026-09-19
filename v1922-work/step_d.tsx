
      {/* Sticky CTA: always reachable, never below a wall of scrolling. */}
      <div className="trial-sticky-cta" data-testid="trial-sticky-cta">
        {step > 1 && (
          <button
            type="button"
            className="v8-outline-button"
            data-testid="trial-back"
            disabled={busy}
            onClick={() => setStep((current) => (current === 3 ? 2 : 1))}
          >
            {zh ? "返回" : "Back"}
          </button>
        )}
        {step < 3 && (
          <button
            type="button"
            className="v8-primary-button"
            data-testid="trial-next"
            disabled={(step === 1 && !step1Ready) || (step === 2 && !step2Ready)}
            onClick={() => setStep((current) => (current === 1 ? 2 : 3))}
          >
            {zh ? "下一步" : "Next"}
          </button>
        )}
        {step === 3 && (
          <button
            type="button"
            className="v8-primary-button"
            data-testid="trial-create"
            disabled={busy}
            onClick={() => void submit()}
          >
            {busy ? t("trial.creating") : zh ? "确认创建" : "Create trip"}
          </button>
        )}
      </div>

      {/* Secondary, de-emphasised: the sealed demo is not the golden path. */}
      <div className="trial-secondary">
        <button
          type="button"
          className="trial-back-link"
          data-testid="trial-tianjin-demo"
          disabled={busy}
          onClick={() => void onUseTianjinDemo()}
        >
          {t("trial.tianjinDemo")}
        </button>
        {step === 1 && (
          <button
            type="button"
            className="trial-back-link"
            data-testid="trial-show-advanced"
            onClick={() => {
              setAdvanced(true);
              const node = document.querySelector(".trial-advanced") as HTMLDetailsElement | null;
              if (node) node.open = true;
            }}
          >
            {zh ? "高级设置" : "Advanced settings"}
          </button>
        )}
      </div>
    </section>
  );
}
