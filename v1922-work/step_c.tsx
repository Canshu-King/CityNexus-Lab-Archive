
      {step === 2 && (
        <div className="v8-card trial-card" data-testid="trial-step2-body">
          <div className="trial-row">
            <label className="trial-field">
              <span>{zh ? "旅行人数" : "Travellers"}</span>
              <input
                data-testid="trial-party"
                type="number"
                min="1"
                max="20"
                value={draft.partySize}
                onChange={(event) => {
                  const partySize = Number(event.target.value);
                  setDraft((current) => ({
                    ...current,
                    partySize,
                    ...(roomsTouched ? {} : { rooms: suggestedRoomCount(partySize) }),
                  }));
                }}
              />
            </label>
            <label className="trial-field">
              <span>{t("trial.rooms")}</span>
              <input
                data-testid="trial-rooms"
                type="number"
                min="1"
                max="20"
                value={draft.rooms}
                onChange={(event) => {
                  setRoomsTouched(true);
                  update("rooms", Number(event.target.value));
                }}
              />
            </label>
          </div>

          <div className="trial-row">
            <label className="trial-field">
              <span>{zh ? "总预算" : "Total budget"}</span>
              <input
                data-testid="trial-budget"
                type="number"
                min="0"
                value={draft.budgetMajor}
                onChange={(event) => update("budgetMajor", Number(event.target.value))}
              />
            </label>
            <label className="trial-field">
              <span>{t("trial.stayBudget")}</span>
              <input
                data-testid="trial-stay-budget"
                type="number"
                min="0"
                value={draft.stayBudgetMajor}
                onChange={(event) => update("stayBudgetMajor", Number(event.target.value))}
              />
            </label>
          </div>

          <fieldset className="trial-fieldset">
            <legend>{zh ? "旅行节奏" : "Pace"}</legend>
            <div className="trial-chips">
              {PACE_OPTIONS.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  className={draft.pace === option.key ? "active" : ""}
                  data-testid={`trial-pace-${option.key}`}
                  onClick={() => update("pace", option.key)}
                >
                  {zh ? option.zh : option.en}
                </button>
              ))}
            </div>
          </fieldset>

          <fieldset className="trial-fieldset">
            <legend>{zh ? "兴趣" : "Interests"}</legend>
            <div className="trial-chips">
              {INTEREST_OPTIONS.map((option) => {
                const selected = (draft.interests ?? []).includes(option.key);
                return (
                  <button
                    key={option.key}
                    type="button"
                    className={selected ? "active" : ""}
                    data-testid={`trial-interest-${option.key}`}
                    onClick={() =>
                      update(
                        "interests",
                        selected
                          ? (draft.interests ?? []).filter((item) => item !== option.key)
                          : [...(draft.interests ?? []), option.key],
                      )
                    }
                  >
                    {zh ? option.zh : option.en}
                  </button>
                );
              })}
            </div>
          </fieldset>

          <label className="trial-field">
            <span>{zh ? "特殊要求" : "Special requirements"}</span>
            <textarea
              data-testid="trial-special"
              rows={3}
              value={draft.specialRequirements ?? ""}
              onChange={(event) => update("specialRequirements", event.target.value)}
              placeholder={
                zh
                  ? "例如：我妈妈坐轮椅；每天走路不超过 3000 米"
                  : "e.g. my mother uses a wheelchair; no more than 3 km walking a day"
              }
            />
          </label>
        </div>
      )}

      {step === 3 && (
        <div className="v8-card trial-card" data-testid="trial-step3-body">
          <dl className="trial-review">
            <div>
              <dt>{zh ? "目的地" : "Destination"}</dt>
              <dd data-testid="review-city">{draft.cityName || "—"}</dd>
            </div>
            <div>
              <dt>{zh ? "抵达" : "Arrival"}</dt>
              <dd data-testid="review-arrival">
                {draft.arrivalLocation || "—"} · {draft.startAt.replace("T", " ")}
              </dd>
            </div>
            <div>
              <dt>{zh ? "离开" : "Departure"}</dt>
              <dd data-testid="review-departure">
                {draft.departureLocation || "—"} · {draft.endAt.replace("T", " ")}
              </dd>
            </div>
            <div>
              <dt>{zh ? "人数 / 房间" : "Travellers / rooms"}</dt>
              <dd data-testid="review-party">
                {draft.partySize} · {draft.rooms}
              </dd>
            </div>
            <div>
              <dt>{zh ? "总预算 / 住宿" : "Total / stay budget"}</dt>
              <dd data-testid="review-budget">
                {draft.currency} {draft.budgetMajor} / {draft.stayBudgetMajor}
              </dd>
            </div>
            <div>
              <dt>{zh ? "节奏" : "Pace"}</dt>
              <dd data-testid="review-pace">{draft.pace || "—"}</dd>
            </div>
            <div>
              <dt>{zh ? "兴趣" : "Interests"}</dt>
              <dd data-testid="review-interests">
                {(draft.interests ?? []).join(", ") || "—"}
              </dd>
            </div>
            <div>
              <dt>{zh ? "特殊要求" : "Special requirements"}</dt>
              <dd data-testid="review-special">{draft.specialRequirements || "—"}</dd>
            </div>
            <div>
              <dt>{zh ? "自动设置" : "Auto-set"}</dt>
              <dd>
                {draft.countryCode} · {draft.currency} · {draft.timezone}
              </dd>
            </div>
          </dl>
          {onCancel && (
            <button type="button" className="trial-back-link" onClick={onCancel}>
              {t("trial.cancel")}
            </button>
          )}
        </div>
      )}
