
      {disruptions.length > 0 && (
        <div className="live-disruption" data-testid="live-disruption" role="status">
          <b>{zh ? "发生了什么" : "What happened"}</b>
          <ul>
            {disruptions.slice(0, 3).map((d) => {
              const copy = EVENT_COPY[d.type] ?? EVENT_COPY.OTHER;
              const affected = activities.find((a) => a.id === d.affected_activity_id);
              return (
                <li key={d.id}>
                  {zh ? copy.zh : copy.en}
                  {affected ? (
                    <span className="live-affected" data-testid="live-affected">
                      {zh ? " · 受影响：" : " · Affected: "}
                      {String(affected.title ?? "")}
                    </span>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {pending.length > 0 ? (
        pending.map((proposal) => {
          const removed = proposal.diff?.removed ?? [];
          const added = proposal.diff?.added ?? [];
          return (
            <article className="live-proposal" key={proposal.id} data-testid="live-proposal">
              <b>{zh ? "推荐怎么改" : "Suggested change"}</b>
              <p className="live-unchanged" data-testid="live-unchanged">
                {proposal.locked_commitments_preserved
                  ? zh
                    ? "已确认的预订和到达/离开时间保持不变。"
                    : "Confirmed bookings and your arrival/departure stay unchanged."
                  : zh
                    ? "注意：部分已确认内容会受影响。"
                    : "Note: some confirmed items are affected."}
              </p>
              {(removed.length > 0 || added.length > 0) && (
                <p className="live-diff">
                  {removed.length > 0 && (
                    <span>{zh ? `移除 ${removed.length} 项 · ` : `Remove ${removed.length} · `}</span>
                  )}
                  {added.length > 0 && (
                    <span>{zh ? `新增 ${added.length} 项` : `Add ${added.length}`}</span>
                  )}
                </p>
              )}
              <div className="live-actions">
                <button
                  type="button"
                  className="v8-primary-button"
                  data-testid="live-accept"
                  disabled={busy !== null}
                  onClick={() => void accept(proposal.id)}
                >
                  {busy === proposal.id
                    ? zh ? "应用中…" : "Applying…"
                    : zh ? "接受新方案" : "Accept new plan"}
                </button>
                <button
                  type="button"
                  className="v8-outline-button"
                  data-testid="live-today-only"
                  disabled={busy !== null}
                  onClick={() =>
                    setMessage(
                      zh ? "只调整今天：已记录，今天的安排会优先。" : "Adjust today only: noted.",
                    )
                  }
                >
                  {zh ? "仅调整今天" : "Adjust today only"}
                </button>
                <button
                  type="button"
                  className="v8-outline-button"
                  data-testid="live-remind-later"
                  disabled={busy !== null}
                  onClick={defer}
                >
                  {zh ? "稍后提醒" : "Remind me later"}
                </button>
              </div>
            </article>
          );
        })
      ) : (
        <p className="v8-muted" data-testid="live-no-proposal">
          {zh ? "当前没有需要你决定的调整。" : "There is nothing for you to decide right now."}
        </p>
      )}

      {message && (
        <p className="role-alert" role="status" data-testid="live-message">
          {message}
        </p>
      )}
    </section>
  );
}
