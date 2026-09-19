
      <div className="trip-day-strip" data-testid="trip-day-strip">
        {visible.map((day, index) => {
          const globalIndex = showWeeks ? week * 7 + index : index;
          return (
            <button
              key={day.key}
              type="button"
              className={globalIndex === activeDay ? "active" : ""}
              data-testid={`trip-day-${globalIndex}`}
              onClick={() => setActiveDay(globalIndex)}
            >
              <span>{day.label}</span>
              <small>
                {zh ? `${day.activities.length} 项` : `${day.activities.length} stops`}
              </small>
            </button>
          );
        })}
      </div>

      {visible.map((day, index) => {
        const globalIndex = showWeeks ? week * 7 + index : index;
        if (globalIndex !== activeDay) return null;
        return (
          <div className="trip-day-detail" key={day.key} data-testid="trip-day-detail">
            {day.activities.map((activity) => {
              const duration = minutesBetween(activity.start_at, activity.end_at);
              const isCurrent = plan.current_activity_id === activity.id;
              const disrupted =
                plan.disruptions?.some((event) => event.affected_activity_id === activity.id) ??
                false;
              return (
                <article
                  key={activity.id}
                  className={`trip-stop${activity.protected ? " protected" : ""}${
                    isCurrent ? " current" : ""
                  }${disrupted ? " disrupted" : ""}`}
                  data-testid="trip-stop"
                >
                  <div className="trip-stop-time">
                    <b>{clock(activity.start_at, tz)}</b>
                    <small>{clock(activity.end_at, tz)}</small>
                  </div>
                  <div className="trip-stop-body">
                    <b>{activity.title}</b>
                    <div className="trip-stop-meta">
                      {duration != null && (
                        <span>
                          {duration >= 60
                            ? zh
                              ? `${Math.floor(duration / 60)} 小时${duration % 60 ? ` ${duration % 60} 分` : ""}`
                              : `${Math.floor(duration / 60)}h${duration % 60 ? ` ${duration % 60}m` : ""}`
                            : zh
                              ? `${duration} 分钟`
                              : `${duration} min`}
                        </span>
                      )}
                      {activity.type && activity.type !== "visit" && (
                        <span className="trip-stop-type">{activity.type}</span>
                      )}
                      {activity.protected && (
                        <span className="trip-stop-protected" data-testid="trip-stop-protected">
                          {zh ? "已确认 · 受保护" : "Confirmed · protected"}
                        </span>
                      )}
                      {disrupted && (
                        <span className="trip-stop-disrupted">
                          {zh ? "受影响" : "Affected"}
                        </span>
                      )}
                      {isCurrent && (
                        <span className="trip-stop-current">{zh ? "当前" : "Now"}</span>
                      )}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        );
      })}
    </section>
  );
}
